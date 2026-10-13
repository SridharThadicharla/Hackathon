# 17 – Negative Scenarios, Resilience & Recovery Matrix

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0)  

---

## 1. Comprehensive Negative Scenario Matrix

| # | Edge Case / Failure Scenario | Expected Architectural Behavior | Actual Code Implementation | Expected HTTP Status | Database Effect | Notification Effect | Verification Method | Status |
|---|---|---|---|---|---|---|---|---|
| **1** | **Missing or Invalid Carrier Auth** | Immediate rejection before business logic runs. | `subflow-validate-carrier-auth` checks `X-Carrier-Token`. Throws `APP:UNAUTHORIZED`. | `401 Unauthorized` | Zero database reads or writes. | Suppressed. | MUnit Test 3 & Postman Req 14. | **IMPLEMENTED AND VERIFIED** |
| **2** | **Malformed JSON Payload** | Immediate edge rejection. | APIKit Router parses JSON against schema. Throws `APIKIT:BAD_REQUEST`. | `400 Bad Request` | Zero database mutation. | Suppressed. | Send `{ broken: json }` in Postman. | **IMPLEMENTED AND VERIFIED** |
| **3** | **Unsupported Courier Code** | Reject unrecognized carrier in URI path. | URI parameter validated against `['BLUEDART', 'DELHIVERY']`. Throws `APP:UNAUTHORIZED`. | `401 Unauthorized` / `400 Bad Request` | Zero database mutation. | Suppressed. | Postman Req 15 (`/webhooks/carriers/FEDEX`). | **IMPLEMENTED AND VERIFIED** |
| **4** | **Unmapped Carrier Status Code** | Graceful fallback without runtime crash. | `normalizedStatusMap[rawStatus] default "UNKNOWN_STATUS"`. | `200 OK` | Recorded in `shipment_tracking_events` with `original_status`. Master status not mutated. | Suppressed (`UNKNOWN_STATUS` is non-milestone). | MUnit Test 5 (`status_code: "CUSTOMS_SPECIAL"`). | **IMPLEMENTED AND VERIFIED** |
| **5** | **Unknown / Unmanifested Tracking Number** | Do not drop event; buffer for future replay. | `subflow-lookup-shipment-by-tracking` finds 0 rows $\rightarrow$ routes to `subflow-quarantine-unknown-shipment`. | `200 OK` (`QUARANTINED_PENDING_REGISTRATION`) | Stored in `pending_tracking_events` with `processing_status = 'PENDING'`. | Suppressed. | MUnit Test 7 & Postman Req 5. | **IMPLEMENTED AND VERIFIED** |
| **6** | **Duplicate Webhook Delivery** | Enforce strict idempotency under courier retry. | `subflow-check-duplicate-event` finds existing `eventKey`. | `200 OK` (`DUPLICATE_ACKNOWLEDGED`) | Zero database mutation. | Suppressed. | MUnit Test 6 & Postman Req 3. | **IMPLEMENTED AND VERIFIED** |
| **7** | **Out-of-Order / Stale Scan** | Prevent backward status rollback. | `shipment-processing.xml` checks `isOlder` or `isDowngrade`. Sets `isOutOfOrder = true`. | `200 OK` (`OUT_OF_ORDER_RECORDED`) | Appended to `shipment_tracking_events` for audit. Master status preserved. | Suppressed. | Postman Req 4 (stale scan for `SHP-1001`). | **IMPLEMENTED AND VERIFIED** |
| **8** | **Scan Received After Terminal State** | Protect `DELIVERED` status from overwrite. | `isTerminal = (current_status == "DELIVERED")`. If `newRank < 50`, flagged as out-of-order downgrade. | `200 OK` (`OUT_OF_ORDER_RECORDED`) | Master status remains `DELIVERED`. Event appended to audit table. | Suppressed. | Postman send `OFD` for delivered parcel. | **IMPLEMENTED AND VERIFIED** |
| **9** | **Missing or Null ETA** | Do not crash risk engine. | `parseDtSafe` function handles null safely with DataWeave `try()`. | `200 OK` | `estimated_delivery_time` set to `NULL`. Risk engine falls back to `STALE_TRANSIT` evaluation. | Normal processing. | Send payload with `"eta": null`. | **IMPLEMENTED AND VERIFIED** |
| **10** | **Database Unavailable (MySQL Down)** | Do not falsely acknowledge; allow carrier retry. | Database connector throws `DB:CONNECTIVITY`. Caught by `globalError_Handler`. | `503 Service Unavailable` | Zero state saved. | Suppressed. | Stop MySQL service and trigger webhook. | **IMPLEMENTED AND VERIFIED** |
| **11** | **VM Queue Failure** | Decouple ingestion from queue errors. | Caught by `globalError_Handler` as `VM:CONNECTIVITY`. | `503 Service Unavailable` | Transaction safely aborted. | Suppressed. | Simulate queue broker offline. | **IMPLEMENTED AND VERIFIED** |
| **12** | **External SMTP Server Unreachable** | Graceful degradation of optional email alerts. | `<email:send>` wrapped in `<try>` with `<on-error-continue>`. Logs warning. | N/A (Asynchronous queue consumer) | Outbox row preserved with `status = 'QUEUED'`. | Logs SMTP warning; consumer thread does not crash. | Set `notification.email.host: "invalid.smtp"`. | **IMPLEMENTED AND VERIFIED** |
| **13** | **Non-Milestone Scan (`IN_TRANSIT`)** | Prevent customer notification spam. | `subflow-publish-milestone-notification` filters milestones. Non-milestones log suppression. | `200 OK` | Master status and audit table updated normally. | **Suppressed by design**. | Postman Req 1 (BlueDart `IT` scan). | **IMPLEMENTED AND VERIFIED** |
| **14** | **Query Non-Existent Shipment** | Clean error handling on REST lookup. | `subflow-select-shipment-by-id` returns 0 rows $\rightarrow$ throws `APP:NOT_FOUND`. | `404 Not Found` | No mutation. | N/A | Postman Req 16. | **IMPLEMENTED AND VERIFIED** |

---

## 2. In-Depth Operational Recovery Procedures

### 1. Recovering From Quarantined Scans (Auto-Reconciliation)
1. **Trigger**: An unmanifested parcel (e.g., `DELH-99887766`) arrives and is safely held in `pending_tracking_events`.
2. **Action**: The WMS manifests the shipment via `POST /api/v1/shipments`.
3. **Recovery**: Call `POST /api/v1/events/reconcile`.
   - The batch flow queries all `pending_tracking_events` where `tracking_number` now exists in `shipments`.
   - Each event is replayed through `flow-process-canonical-event`.
   - Status updates in `pending_tracking_events` from `'PENDING'` to `'RECONCILED'`.

### 2. Recovering From Stale/Out-of-Order Webhook Bursts
1. If an offline delivery van uploads 50 delayed scans after parcels were delivered:
   - The Control Tower accepts all 50 scans with HTTP 200 (`OUT_OF_ORDER_RECORDED`).
   - All 50 scans appear in `GET /shipments/{id}/history` for carrier billing audit.
   - None of the 50 scans overwrite `DELIVERED` status in `shipments`.
   - Zero customer alert emails are sent.
