# 12 – End-to-End Execution Traces: Happy Path & Alternative Scenarios

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0)  

---

## 1. Complete Happy Path Execution Walkthrough

### Scenario: Delhivery Ingests Milestone Scan `OUT_FOR_DELIVERY` for `DELH-11223344`

#### 1. Inbound HTTP Webhook Request
- **Method & URL**: `POST http://localhost:8081/api/v1/webhooks/carriers/DELHIVERY`
- **Headers**:
  ```http
  Content-Type: application/json
  X-Carrier-Token: delhivery-webhook-secret-key-2026
  X-Correlation-ID: DEMO-HAPPY-PATH-101
  ```
- **Body**:
  ```json
  {
    "waybill": "DELH-11223344",
    "Status": {
      "status": "Out for Delivery",
      "statusCode": "OFD",
      "statusDateTime": "2026-10-13 08:30:00",
      "instructions": "Out for delivery with courier agent Ram"
    },
    "Scans": [
      {
        "scanType": "Van Out",
        "scanDateTime": "2026-10-13 08:30:00",
        "scannedLocation": "HYD/BEGUMPET"
      }
    ],
    "ExpectedDeliveryDate": "2026-10-13T18:00:00Z"
  }
  ```

#### 2. Authentication & Ingress Logging
- `shipment-tracking-main` sets `vars.correlationId = "DEMO-HAPPY-PATH-101"`.
- Logs: `[HTTP Ingress] POST /api/v1/webhooks/carriers/DELHIVERY | CorrelationId: DEMO-HAPPY-PATH-101`.
- `subflow-validate-carrier-auth` verifies `X-Carrier-Token` matches `carrier.delhivery.token`. Verification succeeds.

#### 3. Normalization to Canonical Model
- `subflow-normalize-delhivery` runs `dw/delhivery-to-canonical.dwl`.
- Status `OFD` maps to canonical status `OUT_FOR_DELIVERY`.
- Synthesizes `eventKey: "DELHIVERY-DELH-11223344-OFD-20261013083000"`.
- Converts timestamp to UTC ISO-8601: `"2026-10-13T03:00:00Z"`.

#### 4. Deduplication & Master Lookup
- `subflow-check-duplicate-event` queries MySQL with `event_key`. Returns 0 rows $\rightarrow$ Unique event.
- `subflow-lookup-shipment-by-tracking` queries `shipments` for `DELH-11223344`. Found: `SHP-1002`, `current_status = 'PICKED_UP'` (Rank 20).

#### 5. Anti-Regression & Status Progression Decision
- Current Rank: `20` (`PICKED_UP`).
- Incoming Rank: `40` (`OUT_FOR_DELIVERY`).
- Rule Evaluation: `40 > 20` and package is not terminal $\rightarrow$ **Valid Forward Progression**.

#### 6. Explainable Risk Assessment
- `subflow-evaluate-eta-and-delay` compares ETA (`2026-10-13T18:00:00Z`) against promised SLA (`2026-10-14 20:00:00Z`).
- ETA is within promised deadline $\rightarrow$ `vars.riskAssessment = { riskLevel: "ON_TRACK", explanation: "Shipment progressing normally within SLA." }`.

#### 7. Transactional Database Write
- `subflow-update-shipment-status-and-event` executes atomic update:
  - Updates `shipments`: `current_status = 'OUT_FOR_DELIVERY'`, `status_rank = 40`, `risk_level = 'ON_TRACK'`.
  - Appends to `shipment_tracking_events`: `processing_result = 'PROCESSED'`.

#### 8. Transactional Outbox & Queue Publishing
- `subflow-publish-milestone-notification` evaluates status `OUT_FOR_DELIVERY` against milestone list $\rightarrow$ **Eligible**.
- Inserts row into `notification_outbox` with `status = 'QUEUED'`.
- Publishes message payload to persistent VM queue `shipment-milestone-queue`.

#### 9. Webhook Synchronous Response (`<50ms`)
- Courier receives HTTP `200 OK`:
  ```json
  {
    "success": true,
    "status": "EVENT_PROCESSED_SUCCESSFULLY",
    "message": "Out for delivery! Your package is with our delivery agent and will arrive today.",
    "customerMessage": "Out for delivery! Your package is with our delivery agent and will arrive today.",
    "customerNotification": {
      "milestone": "OUT_FOR_DELIVERY",
      "recipientEmail": "customer@control-tower-logistics.com",
      "status": "DISPATCHED_TO_CUSTOMER",
      "notificationId": "NOTIF-d3814838"
    },
    "eventId": "EVT-DEL-20261013083000",
    "shipmentId": "SHP-1002",
    "trackingNumber": "DELH-11223344",
    "carrier": "DELHIVERY",
    "normalizedStatus": "OUT_FOR_DELIVERY",
    "isDuplicate": false,
    "isOutOfOrder": false,
    "isPendingUnknown": false,
    "receivedTimestamp": "2026-10-13T08:30:02Z",
    "correlationId": "DEMO-HAPPY-PATH-101"
  }
  ```

#### 10. Asynchronous Queue Consumer Execution
- `flow-consume-milestone-notification` picks up message from `shipment-milestone-queue`.
- Renders styled HTML card template.
- Transmits email via SMTP (or console simulation if disabled).
- Updates `notification_outbox` status to `'SENT'` and `sent_at = NOW()`.

---

## 2. Tracing Alternative & Edge-Case Execution Paths

### Path A: Duplicate Event Arrival (Idempotency)
1. Carrier resends the exact same payload above with identical scan timestamp.
2. `dw/delhivery-to-canonical.dwl` generates the exact same `eventKey: "DELHIVERY-DELH-11223344-OFD-20261013083000"`.
3. `subflow-check-duplicate-event` queries MySQL. Match found (`id: 12`)!
4. `vars.isDuplicate` set to `true`.
5. Choice router bypasses database writes, risk calculations, and VM queues entirely.
6. Returns HTTP `200 OK`:
   ```json
   {
     "success": true,
     "status": "DUPLICATE_ACKNOWLEDGED",
     "message": "Event already processed and recorded. Duplicate delivery suppressed safely.",
     "isDuplicate": true,
     "isOutOfOrder": false
   }
   ```
7. Result: Zero duplicate emails, zero corrupted audit rows.

---

### Path B: Out-of-Order Stale Scan Arrival (Anti-Regression)
1. Carrier sends an older pickup scan (`status_code: "PU"`, timestamp: `2026-10-10 08:00:00`) for a parcel currently in `DELIVERED` status.
2. Anti-regression engine evaluates:
   `isDowngrade = (current_status == "DELIVERED") and (newRank < currentRank)`.
   `newRank (20) < currentRank (50)` $\rightarrow$ `isDowngrade = true`.
3. Application logs: `[Out-of-Order] Stale/Older event received... Preserving in history without regressing current status: DELIVERED`.
4. Executes `subflow-insert-tracking-event` with `processing_result = 'OUT_OF_ORDER_RECORDED'` (audit trail preserved).
5. **Does NOT update `shipments` master table**. Status remains `DELIVERED`.
6. Suppresses customer milestone notifications.
7. Returns HTTP `200 OK` with `status: "OUT_OF_ORDER_RECORDED"`.

---

### Path C: Unmanifested Parcel Arrival (Quarantine Buffer)
1. Carrier sends scan for waybill `DELH-99887766` which does not exist in `shipments` table yet.
2. `subflow-lookup-shipment-by-tracking` returns 0 rows.
3. Choice router branches to `subflow-quarantine-unknown-shipment`.
4. Saves raw JSON payload into `pending_tracking_events` with `processing_status = 'PENDING'`.
5. Returns HTTP `200 OK`:
   ```json
   {
     "success": true,
     "status": "QUARANTINED_PENDING_REGISTRATION",
     "message": "Shipment record not found in master database. Event safely quarantined for auto-reconciliation.",
     "isPendingUnknown": true
   }
   ```
6. Result: Carrier does not receive an error; parcel scan is preserved for automated batch replay.

---

### Path D: Routine Transit Hop (Milestone Notification Suppression)
1. BlueDart sends in-transit scan (`status_code: "IT"`).
2. Status updates to `IN_TRANSIT` in `shipments` and audit ledger.
3. `subflow-publish-milestone-notification` evaluates:
   `['PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'EXCEPTION'] contains 'IN_TRANSIT'` $\rightarrow$ **FALSE**.
4. Logs: `[CUSTOMER NOTIFICATION SUPPRESSED (BY DESIGN)] Reason: Status "IN_TRANSIT" is an internal transit hop`.
5. Skips queue publishing and email dispatch.
6. Result: Customer does not receive notification spam for intermediate hub scans.
