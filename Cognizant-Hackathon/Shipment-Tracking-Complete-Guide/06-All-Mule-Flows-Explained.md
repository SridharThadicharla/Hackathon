# 06 – All Mule Flows Explained: Complete Architecture Reference

**Project**: Shipment Signal Control Tower  
**Mule Version**: Mule 4.12.1 / 4.4.x  
**Configuration Directory**: `src/main/mule/`  

---

## 1. Flow Inventory by Configuration File

The application is structured into 8 modular XML configuration files. Every flow and subflow has a dedicated, single responsibility:

| Configuration File | Implemented Flows & Subflows | Responsibility |
|---|---|---|
| `global-config.xml` | Global configurations | HTTP Listener, MySQL connection, VM persistent queues, APIKit Router |
| `webhook-api.xml` | 13 Flows / Subflows | Inbound HTTP listener, APIKit endpoints, carrier authentication |
| `carrier-normalization.xml` | 3 Subflows | BlueDart, Delhivery normalizers, and carrier router |
| `shipment-processing.xml` | 1 Core Flow | Deduplication, quarantine, out-of-order check, state progression |
| `risk-assessment.xml` | 1 Subflow | Explainable delay risk score & SLA deadline computation |
| `notification-queue.xml` | 1 Subflow + 1 Flow | Transactional outbox persistence, VM publishing, and asynchronous consumer |
| `database-operations.xml` | 13 Subflows | Parameterized SQL queries for all 5 MySQL database tables |
| `error-handling.xml` | 1 Global Handler | RFC-7807 error translation for 400, 401, 404, 405, 500, 503 |

---

## 2. Ingress & Routing Flows (`webhook-api.xml`)

### Flow 1: `shipment-tracking-main`
- **File**: `webhook-api.xml`
- **Purpose**: Central HTTP ingress gateway for all `/api/v1/*` requests.
- **Processing Sequence**:
  1. Receives inbound HTTP request via `HTTP_Listener_config` on `0.0.0.0:8081`.
  2. Extracts or generates distributed tracing UUID:
     `vars.correlationId = attributes.headers['x-correlation-id'] default uuid()`.
  3. Logs inbound HTTP method, path, and Correlation ID.
  4. Dispatches request to `<apikit:router config-ref="shipment-tracking-config" />`.
  5. Catches any unhandled exceptions with `<error-handler ref="globalError_Handler" />`.
- **Response Headers**: Sets `X-Correlation-ID` and `Content-Type: application/json`.

---

### Subflow 2: `subflow-validate-carrier-auth`
- **File**: `webhook-api.xml`
- **Purpose**: Authenticates carrier push requests against pre-shared secret tokens.
- **Input**: `attributes.headers['x-carrier-token']` or query parameter `x-carrier-token`.
- **Logic**:
  - If `vars.carrier == 'BLUEDART'`: compares token to `p('carrier.bluedart.token')` (`bluedart-webhook-secret-key-2026`).
  - If `vars.carrier == 'DELHIVERY'`: compares token to `p('carrier.delhivery.token')` (`delhivery-webhook-secret-key-2026`).
  - If token does not match: logs warning and executes:
    `<raise-error type="APP:UNAUTHORIZED" description="Invalid or missing X-Carrier-Token header" />`.

---

### Flow 3: `post:\webhooks\carriers\(carrierCode):application\json:shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: The official Use Case 08 endpoint accepting webhooks for any carrier code in URI.
- **Processing Sequence**:
  ```text
  Extract URI Param {carrierCode}
      -> Set vars.carrier = upper(trim(attributes.uriParams.'carrierCode'))
      -> flow-ref: subflow-validate-carrier-auth
      -> flow-ref: subflow-route-carrier-normalization
      -> flow-ref: flow-process-canonical-event
  ```
- **Input Payload**: Raw JSON from courier (BlueDart or Delhivery format).
- **Output**: JSON `WebhookAcknowledgment` with HTTP 200.

---

### Flow 4 & 5: `post:\webhooks\bluedart:...` and `post:\webhooks\delhivery:...`
- **File**: `webhook-api.xml`
- **Purpose**: Direct carrier webhook aliases for dedicated courier webhook routing.
- **Sequence**: Sets `vars.carrier`, validates token, executes carrier normalizer, and routes to canonical event processor.

---

### Flow 6: `post:\shipments:application\json:shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: Registers a new package manifested in the WMS or ERP.
- **Input Payload**: `shipmentId`, `trackingNumber`, `carrier`, `originLocation`, `destinationLocation`, `promisedDeliveryTime`.
- **Database Operation**: Executes SQL `INSERT INTO shipments (...) VALUES (...) ON DUPLICATE KEY UPDATE ...`.
- **Output**: HTTP 201 Created with full `ShipmentDetail` JSON.

---

### Flow 7: `get:\shipments\(trackingNumber):shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: Queries current shipment state and SLA risk by tracking number or shipment ID.
- **Database Operation**: Selects record from `shipments` table matching `shipment_id` or `tracking_number`.
- **Error**: If record not found, raises `APP:NOT_FOUND` (HTTP 404).

---

### Flow 8: `get:\shipments\(trackingNumber)\history:shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: Returns the full chronological event trail from `shipment_tracking_events`.
- **Output**: Array of `ShipmentEvent` objects ordered by `event_timestamp ASC`.

---

### Flow 9: `get:\shipments\(trackingNumber)\risk:shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: On-demand computation of explainable delay risk against promised customer SLA.
- **Sequence**: Fetches shipment record, runs `subflow-evaluate-eta-and-delay`, returns `RiskAssessment` JSON.

---

### Flow 10: `get:\health:shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: Operational health probe for load balancers and Kubernetes readiness probes.
- **Operations**: Executes `SELECT 1 AS healthy;` against MySQL database and verifies queue readiness.
- **Output**: HTTP 200 with `{ status: "UP", database: "CONNECTED", queue: "CONNECTED" }`.

---

### Flow 11: `get:\carriers\pulse:shipment-tracking-config`
- **File**: `webhook-api.xml`
- **Purpose**: Operational telemetry aggregating total received events, processed scans, duplicate count, out-of-order count, and active shipments per carrier.

---

### Flow 12 & 13: `post:\events\replay` and `post:\events\reconcile`
- **File**: `webhook-api.xml`
- **Purpose**:
  - `/events/replay`: Operator single-event replay from quarantine table `pending_tracking_events`.
  - `/events/reconcile`: Automated batch reconciliation finding pending scans where master shipment records have now been created, reprocessing them through the canonical pipeline.

---

## 3. Normalization Subflows (`carrier-normalization.xml`)

### Subflow 14: `subflow-normalize-bluedart`
- **File**: `carrier-normalization.xml`
- **Transformation**: Executes `dw/bluedart-to-canonical.dwl`.
- **Input**: BlueDart payload (`awb_no`, `status_code`, `scan_date_time`, `eta`, etc.).
- **Output**: Standardized Canonical Event dictionary in `payload`.

### Subflow 15: `subflow-normalize-delhivery`
- **File**: `carrier-normalization.xml`
- **Transformation**: Executes `dw/delhivery-to-canonical.dwl`.
- **Input**: Delhivery payload (`waybill`, `Status`, `Scans`, `ExpectedDeliveryDate`).
- **Output**: Standardized Canonical Event dictionary in `payload`.

### Subflow 16: `subflow-route-carrier-normalization`
- **File**: `carrier-normalization.xml`
- **Routing**: Choice router evaluating `upper(trim(vars.carrier))`:
  - `BLUEDART` -> calls `subflow-normalize-bluedart`
  - `DELHIVERY` -> calls `subflow-normalize-delhivery`
  - Otherwise -> raises `APP:UNSUPPORTED_CARRIER` (HTTP 400).

---

## 4. Event Processing Pipeline (`shipment-processing.xml`)

### Flow 17: `flow-process-canonical-event`
- **File**: `shipment-processing.xml`
- **The Core Control Tower Pipeline**:
  ```text
  1. Store payload as vars.canonicalEvent
  2. subflow-select-event-by-key (Idempotency Query)
     │
     ├── IF duplicate exists:
     │   └── Set vars.isDuplicate = true
     │   └── Return DUPLICATE_ACKNOWLEDGED response (suppress DB & alerts)
     │
     └── ELSE (Fresh Event):
         └── subflow-select-shipment-by-tracking-number
             │
             ├── IF shipment NOT found in DB:
             │   └── Set vars.isPendingUnknown = true
             │   └── subflow-insert-pending-event (Quarantine to pending_tracking_events)
             │   └── Return QUARANTINED_PENDING_REGISTRATION response
             │
             └── IF shipment found:
                 └── Evaluate rank & timestamp chronology
                     │
                     ├── IF out-of-order / stale:
                     │   └── Set vars.isOutOfOrder = true
                     │   └── subflow-insert-tracking-event (Save to audit with OUT_OF_ORDER_RECORDED)
                     │   └── Return OUT_OF_ORDER_RECORDED response (NO master state regression)
                     │
                     └── ELSE (Valid forward progression):
                         └── subflow-evaluate-eta-and-delay (Compute Risk Level)
                         └── subflow-update-shipment-state (Update shipments master record)
                         └── subflow-insert-tracking-event (Save to audit with PROCESSED)
                         └── subflow-publish-milestone-notification (Save to Outbox & VM Queue)
                         └── Return EVENT_PROCESSED_SUCCESSFULLY response
  ```

---

## 5. Delay Risk Engine (`risk-assessment.xml`)

### Subflow 18: `subflow-evaluate-eta-and-delay`
- **File**: `risk-assessment.xml`
- **Rule Hierarchy**:
  1. **Delivered Check**: If status is `DELIVERED` -> `ON_TRACK` ("Delivered successfully").
  2. **Critical Check**: If status is `EXCEPTION` or `DELIVERY_ATTEMPTED` and promised delivery time expired -> `CRITICAL`.
  3. **Delayed Check**: If current time exceeds promised delivery time -> `DELAYED`.
  4. **At-Risk Check**: If carrier revised ETA exceeds promised delivery time -> `AT_RISK`.
  5. **Normal Transit**: If scans progressing within SLA deadline -> `ON_TRACK`.
- **Output**: Sets `vars.riskAssessment` containing `riskLevel`, `reasonCode`, `explanation`, and `riskFactors`.

---

## 6. Messaging & Outbox Subflows (`notification-queue.xml`)

### Subflow 19: `subflow-publish-milestone-notification`
- **File**: `notification-queue.xml`
- **Eligibility Filter**: Status must be in `['PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'EXCEPTION', 'DELIVERY_ATTEMPTED']` AND `isDuplicate == false` AND `isOutOfOrder == false` AND `isPendingUnknown == false`.
- **Step 1**: Builds customer notification message.
- **Step 2**: Calls `subflow-insert-notification-outbox` to persist record in `notification_outbox` table.
- **Step 3**: Publishes message to persistent VM queue `${queue.milestoneQueue}`.

### Flow 20: `flow-consume-milestone-notification`
- **File**: `notification-queue.xml`
- **Listener**: Listens on VM queue `shipment-milestone-queue`.
- **Action**: Simulates multi-channel SMS/Email delivery and calls `subflow-mark-notification-sent` to update outbox record status to `SENT`.
