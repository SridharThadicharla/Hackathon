# 21 – End-to-End API Methods, Headers, Payloads & Hackathon Presentation Guide

**Project**: Shipment Signal Control Tower – Real-Time Multi-Carrier Tracking  
**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  
**Document Purpose**: Complete, definitive reference explaining:
1. How to distinguish **Original** vs **Duplicate** events across API responses, Mule logs, and MySQL database.
2. Why every **HTTP Method**, **URL**, **Header**, and **Body field** is used across the system.
3. A chronological, step-by-step **Hackathon Demo Runbook** to present and run the project flawlessly in front of the judges.

---

## Table of Contents
1. [Deep-Dive: How to Know Which Event is Original vs Duplicate](#1-deep-dive-how-to-know-which-event-is-original-vs-duplicate)
2. [Why We Use Each HTTP Method, URL, Header, and Body](#2-why-we-use-each-http-method-url-header-and-body)
3. [Complete API Catalog: Every Method, URL, Header & Body Explained](#3-complete-api-catalog-every-method-url-header--body-explained)
   - [Request 1: POST BlueDart Webhook – In-Transit Scan (Original)](#request-1-post-bluedart-webhook--in-transit-scan-original)
   - [Request 2: POST Duplicate BlueDart Scan (Idempotency Test)](#request-2-post-duplicate-bluedart-scan-idempotency-test)
   - [Request 3: POST Delhivery Webhook – Out for Delivery Scan (Milestone Notification)](#request-3-post-delhivery-webhook--out-for-delivery-scan-milestone-notification)
   - [Request 4: POST Out-of-Order Stale BlueDart Scan (Non-Regression)](#request-4-post-out-of-order-stale-bluedart-scan-non-regression)
   - [Request 5: POST Unknown Shipment Scan (Quarantine Buffer)](#request-5-post-unknown-shipment-scan-quarantine-buffer)
   - [Request 6: POST Register Master Shipment (WMS Creation)](#request-6-post-register-master-shipment-wms-creation)
   - [Request 7: POST Reconcile Quarantined Events (Auto-Recovery Batch)](#request-7-post-reconcile-quarantined-events-auto-recovery-batch)
   - [Request 8: GET Shipment by Tracking Number (Master State)](#request-8-get-shipment-by-tracking-number-master-state)
   - [Request 9: GET Shipment Event History (Immutable Audit Trail)](#request-9-get-shipment-event-history-immutable-audit-trail)
   - [Request 10: GET Explainable Delay Risk Assessment (SLA Breach Engine)](#request-10-get-explainable-delay-risk-assessment-sla-breach-engine)
   - [Request 11: GET Customer Notification Messages (Transactional Outbox)](#request-11-get-customer-notification-messages-transactional-outbox)
   - [Request 12: GET Operational Health Check (Liveness Probe)](#request-12-get-operational-health-check-liveness-probe)
   - [Request 13: GET Carrier Pulse Telemetry (Control Tower Dashboard Metrics)](#request-13-get-carrier-pulse-telemetry-control-tower-dashboard-metrics)
   - [Request 14: POST Webhook Security Rejection – Invalid Token (401 Unauthorized)](#request-14-post-webhook-security-rejection--invalid-token-401-unauthorized)
   - [Request 15: POST Unsupported Carrier Code (400 Bad Request)](#request-15-post-unsupported-carrier-code-400-bad-request)
   - [Request 16: GET Non-Existent Shipment (404 Not Found)](#request-16-get-non-existent-shipment-404-not-found)
4. [Step-by-Step Hackathon Presentation & Runbook (Start to End)](#4-step-by-step-hackathon-presentation--runbook-start-to-end)

---

## 1. Deep-Dive: How to Know Which Event is Original vs Duplicate

When you send a webhook to `http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`, the Mule application executes an **Idempotency Verification Pattern**.

### Why did you see this log?
```log
WARN  2026-10-11 23:37:27,554 [[MuleRuntime].uber.08: [Shipment-Signal-Control-Tower].flow-process-canonical-event.BLOCKING @4c294534] [event: 9e39aa80-c59e-11f1-a335-f446373582c1] org.mule.runtime.core.internal.processor.LoggerMessageProcessor: [Idempotency] Duplicate event detected and suppressed. EventKey: BLUEDART-BD-123456789-DL-20261011201500 | Tracking: BD-123456789
```

### The Idempotency Key Algorithm
In `src/main/resources/dw/bluedart-to-canonical.dwl` (lines 53–56), the system constructs a deterministic `eventKey`:
```dataweave
var trackingNum = trim(payload.awb_no default payload.awb default payload.tracking_number default "UNKNOWN_AWB")
var compactTs = eventTimeUtc replace /[-:TZ]/ with ""
var eventKeyCalc = "BLUEDART-" ++ trackingNum ++ "-" ++ rawStatus ++ "-" ++ compactTs
```
**Formula**:  
`{CARRIER}-{TRACKING_NUMBER}-{RAW_CARRIER_STATUS}-{COMPACT_SCAN_TIMESTAMP}`  
**Example**:  
`BLUEDART-BD-123456789-DL-20261011201500`

### How the System Knows: 4 Exact Differences

| Verification Layer | 🥇 Original Event (First Time Received) | 🔁 Duplicate Event (Re-transmitted / Repeated) |
|---|---|---|
| **1. Database Query Before Processing** | `SELECT ... FROM shipment_tracking_events WHERE event_key = :eventKey;` returns **0 records**. | Query returns **1 existing record** (`sizeOf(vars.existingEvent) > 0`). |
| **2. HTTP Status & API Response** | **HTTP 200 OK**<br>```json{  "success": true,  "status": "EVENT_PROCESSED_SUCCESSFULLY",  "message": "Shipment event received, normalized, persisted, and evaluated.",  "isDuplicate": false}``` | **HTTP 200 OK**<br>```json{  "success": true,  "status": "DUPLICATE_ACKNOWLEDGED",  "message": "Event already processed and recorded. Duplicate delivery suppressed safely.",  "isDuplicate": true}``` |
| **3. Mule Console Log Output** | `INFO [Normalizer] BlueDart normalized to Canonical Status: DELIVERED | EventKey: BLUEDART-...`<br>Followed by database update and notification enqueueing logs. | `WARN ... [Idempotency] Duplicate event detected and suppressed. EventKey: BLUEDART-BD-123456789-DL-20261011201500 | Tracking: BD-123456789` |
| **4. Database Tables Action** | **Written to DB**: Master `shipments` table is updated with new state. A new immutable row is created in `shipment_tracking_events` with `processing_result = 'PROCESSED'`. | **Suppressed from DB**: Zero new rows created in `shipment_tracking_events`. Zero updates made to `shipments`. |
| **5. Customer Notifications** | If status is a milestone (`DELIVERED`, `OUT_FOR_DELIVERY`), an SMS/Email alert is enqueued in `notification_outbox` and sent. | **Completely Suppressed**: No duplicate customer alerts or SMS messages are sent, preventing customer spam. |

### How You Can Verify Which One It Is in MySQL Workbench
Run this query to check the recorded events:
```sql
SELECT id, event_key, tracking_number, carrier, original_status, 
       normalized_status, processing_result, event_timestamp, received_timestamp 
FROM shipment_tracking_events 
WHERE tracking_number = 'BD-123456789';
```
- **The Original Event** is the **single row** in the table with `processing_result = 'PROCESSED'`.
- **The Duplicate Event** did **not create a second row** because the table has a `UNIQUE KEY uq_events_key (event_key)` and Mule's Choice Router intentionally caught it before insertion.

> [!NOTE]
> **Why did your body say `BD-987654321` while the log said `BD-123456789`?**  
> In your Anypoint Studio console log, the log line you copied was from an earlier test executed for tracking number `BD-123456789` (pre-seeded delayed test shipment). When you send the body with `"awb": "BD-987654321"`, the event key will be `BLUEDART-BD-987654321-DL-20261011163000`. The first time you hit Send it is the **Original**, and the second time you hit Send with the exact same payload it becomes the **Duplicate**.

---

## 2. Why We Use Each HTTP Method, URL, Header, and Body

### 2.1 HTTP Methods

| Method | Why It Is Used in This Project | Example Endpoint |
|---|---|---|
| **POST** | Used for operations that **ingest data**, **alter state**, or **trigger execution**. Carrier webhooks push scan events via HTTP POST. Registering shipments creates new records. Batch reconciliation triggers a workflow. | `POST /api/v1/webhooks/carriers/BLUEDART`<br>`POST /api/v1/shipments`<br>`POST /api/v1/events/reconcile` |
| **GET** | Used for **safe, read-only retrievals**. GET requests never modify database records or state. They fetch master shipment state, event history, risk scores, health, and carrier pulse telemetry. | `GET /api/v1/shipments/BD-987654321`<br>`GET /api/v1/shipments/BD-123456789/risk`<br>`GET /api/v1/health` |

---

### 2.2 URL Paths & Hierarchy

All URLs follow RESTful conventions under the versioned base path `/api/v1/`:
1. `/api/v1/webhooks/carriers/{carrierCode}`:  
   **Why**: A clean, carrier-agnostic ingestion endpoint where `{carrierCode}` (`BLUEDART` or `DELHIVERY`) is dynamically extracted from the URI parameter to route the payload to the correct DataWeave normalizer.
2. `/api/v1/shipments`:  
   **Why**: The collection resource representing master shipment entities registered from Warehouse Management Systems (WMS).
3. `/api/v1/shipments/{trackingNumber}`:  
   **Why**: Specific resource lookup for a package's current status and SLA metrics.
4. `/api/v1/shipments/{trackingNumber}/history`:  
   **Why**: Sub-resource representing the complete, immutable chronological audit trail of scans for that package.
5. `/api/v1/shipments/{trackingNumber}/risk`:  
   **Why**: Specialized operational sub-resource executing the Explainable Delay Risk Engine for predictive SLA breach analysis.
6. `/api/v1/health`:  
   **Why**: Standard DevOps liveness probe checking Mule runtime, MySQL connection, and VM queues.
7. `/api/v1/carriers/pulse`:  
   **Why**: Real-time aggregated telemetry endpoint powering executive dashboards.
8. `/api/v1/events/reconcile`:  
   **Why**: Administrative action triggering auto-reconciliation of quarantined events.

---

### 2.3 HTTP Headers (Why Every Header is Used)

| Header Name | Value Example | Why It Is Used & What It Does | What Happens if Missing/Invalid |
|---|---|---|---|
| **`Content-Type`** | `application/json` | Informs the HTTP listener and APIKit router that the incoming payload is JSON formatted. This allows MuleSoft to parse the stream into structured JSON variables. | If omitted or incorrect (e.g. `text/plain`), APIKit may reject the request with `415 Unsupported Media Type`. |
| **`X-Carrier-Token`** | `bluedart-webhook-secret-key-2026` | **Carrier Webhook Authentication**: Carrier webhook callbacks cannot perform complex interactive OAuth2 login flows. Instead, carriers sign webhook POSTs with a pre-shared secret key. Mule's `subflow-validate-carrier-auth` validates this against secure properties in `mule-dev.yaml`. | If missing or invalid, Mule halts the flow and returns **`401 Unauthorized`**. |
| **`X-Correlation-ID`** | `c85d8984-9df2-43bb-a53f-a3cf6ad35501` | **Distributed Tracing & Observability**: Connects every HTTP request, log message, database audit record, VM queue message, and response together. You can search this single ID across all system logs to trace a package's entire journey. | If omitted by the client, Mule's ingress router automatically generates a new UUID: `#[attributes.headers['x-correlation-id'] default uuid()]`. |
| **`Accept`** | `application/json` | Tells the Mule server that the client expects a JSON response body. | Defaults to `application/json` defined in the RAML specification. |

---

### 2.4 Payload (Body) Fields

Different carriers send different JSON structures. The Control Tower supports carrier-native schemas:

#### BlueDart JSON Payload Fields
- **`awb_no`** (or `awb` / `tracking_number`): The Air Waybill tracking number assigned to the parcel (e.g., `"BD-987654321"`).
- **`status_code`** (or `status`): BlueDart's internal carrier status code (e.g., `"IT"` for In Transit, `"PU"` for Picked Up, `"DL"` for Delivered, `"OFD"` for Out for Delivery).
- **`status_description`**: Human-readable explanation of the scan event from the carrier sorting facility.
- **`scan_date_time`** (or `scan_datetime`): The exact ISO-8601 or formatted date-time string when the physical barcode was scanned at the warehouse/hub.
- **`location_code`**: Carrier facility code (e.g., `"BOM/HUB"`, `"DEL/FC"`).
- **`location_name`**: Human-readable name of the physical transit hub.
- **`eta`**: Carrier's updated estimated delivery time.

#### Delhivery JSON Payload Fields
- **`waybill`**: Delhivery's unique tracking identifier (e.g., `"DELH-11223344"`).
- **`Status.statusCode`**: Delhivery nested status code (e.g., `"OFD"`, `"IT"`, `"DL"`).
- **`Status.status`**: Status string description (e.g., `"Out for Delivery"`).
- **`Status.statusDateTime`**: Timestamp of scan in local format (`"YYYY-MM-DD HH:mm:ss"`).
- **`Scans`**: Array of physical scan milestones recorded along the distribution route.
- **`ExpectedDeliveryDate`**: Delhivery's anticipated delivery date-time.

---

## 3. Complete API Catalog: Every Method, URL, Header & Body Explained

Below is the complete catalog of all 15 API requests included in the Postman collection `postman/Shipment-Tracking.postman_collection.json`.

---

### Request 1: POST BlueDart Webhook – In-Transit Scan (Original)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json` (Declares JSON payload)
  - `X-Carrier-Token`: `bluedart-webhook-secret-key-2026` (Authenticates BlueDart webhook)
  - `X-Correlation-ID`: `c85d8984-9df2-43bb-a53f-a3cf6ad35501` (Trace identifier)
- **Body**:
  ```json
  {
    "awb_no": "BD-987654321",
    "status_code": "IT",
    "status_description": "In Transit - Forwarded to Destination Hub",
    "scan_date_time": "2026-10-11T10:30:00+05:30",
    "location_code": "DEL/HUB",
    "location_name": "Delhi Regional Sorting Hub",
    "eta": "2026-10-14T18:00:00+05:30"
  }
  ```
- **Why this body is used**: Simulates BlueDart pushing an In-Transit barcode scan from their Delhi Sorting Hub for master shipment `SHP-1001`.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "EVENT_PROCESSED_SUCCESSFULLY",
    "message": "Shipment event received, normalized, persisted, and evaluated.",
    "eventId": "EVT-BD-20261011050000",
    "shipmentId": "SHP-1001",
    "trackingNumber": "BD-987654321",
    "carrier": "BLUEDART",
    "normalizedStatus": "IN_TRANSIT",
    "isDuplicate": false,
    "isOutOfOrder": false,
    "isPendingUnknown": false,
    "receivedTimestamp": "2026-10-11T18:14:37Z",
    "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501"
  }
  ```
- **Internal System Actions**:
  1. `subflow-validate-carrier-auth` validates `X-Carrier-Token`.
  2. `bluedart-to-canonical.dwl` normalizes `"IT"` to canonical `"IN_TRANSIT"` and converts timestamp to UTC.
  3. `subflow-select-event-by-key` checks for existing key. Result is 0 rows (Original).
  4. `subflow-select-shipment-by-tracking-number` finds `SHP-1001`.
  5. `subflow-update-shipment-state` updates master shipment `current_status = 'IN_TRANSIT'`, `status_rank = 30`.
  6. `subflow-insert-tracking-event` writes row into `shipment_tracking_events` with `processing_result = 'PROCESSED'`.

---

### Request 2: POST Duplicate BlueDart Scan (Idempotency Test)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `bluedart-webhook-secret-key-2026`
  - `X-Correlation-ID`: `c85d8984-9df2-43bb-a53f-a3cf6ad35501`
- **Body**: (Exact same body as Request 1 above)
- **Why this body is used**: Simulates a network retry where BlueDart delivers the identical webhook scan a second time.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "DUPLICATE_ACKNOWLEDGED",
    "message": "Event already processed and recorded. Duplicate delivery suppressed safely.",
    "eventId": "EVT-BD-20261011050000",
    "shipmentId": "SHP-1001",
    "trackingNumber": "BD-987654321",
    "carrier": "BLUEDART",
    "normalizedStatus": "IN_TRANSIT",
    "isDuplicate": true,
    "isOutOfOrder": false,
    "isPendingUnknown": false,
    "receivedTimestamp": "2026-10-11T18:15:02Z",
    "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501"
  }
  ```
- **Internal System Actions**:
  1. `subflow-select-event-by-key` queries MySQL. Existing row found.
  2. `vars.isDuplicate` set to `true`.
  3. Mule runtime outputs `WARN ... [Idempotency] Duplicate event detected and suppressed.`.
  4. Flow terminates early with acknowledgment response. No duplicate database rows are created.

---

### Request 3: POST Delhivery Webhook – Out for Delivery Scan (Milestone Notification)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/DELHIVERY`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `delhivery-webhook-secret-key-2026` (Authenticates Delhivery)
  - `X-Correlation-ID`: `c85d8984-9df2-43bb-a53f-a3cf6ad35501`
- **Body**:
  ```json
  {
    "waybill": "DELH-11223344",
    "Status": {
      "status": "Out for Delivery",
      "statusCode": "OFD",
      "statusDateTime": "2026-10-11 08:30:00",
      "instructions": "Package out for delivery with courier agent Ram"
    },
    "Scans": [
      {
        "scanType": "Van Out",
        "scanDateTime": "2026-10-11 08:30:00",
        "scannedLocation": "HYD/BEGUMPET"
      }
    ],
    "ExpectedDeliveryDate": "2026-10-11T18:00:00Z"
  }
  ```
- **Why this body is used**: Tests ingestion of Delhivery's nested structure and triggers a **milestone notification** (`OFD` = Out for Delivery).
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "EVENT_PROCESSED_SUCCESSFULLY",
    "message": "Shipment event received, normalized, persisted, and evaluated.",
    "shipmentId": "SHP-1002",
    "trackingNumber": "DELH-11223344",
    "carrier": "DELHIVERY",
    "normalizedStatus": "OUT_FOR_DELIVERY",
    "isDuplicate": false,
    "isOutOfOrder": false,
    "isPendingUnknown": false
  }
  ```
- **Internal System Actions**:
  1. `delhivery-to-canonical.dwl` maps nested `Status.statusCode: "OFD"` to canonical `"OUT_FOR_DELIVERY"`.
  2. Updates `shipments` master table (`status_rank = 40`).
  3. Writes milestone alert record into `notification_outbox` table with status `QUEUED`.
  4. Publishes message to VM Queue `shipment-milestone-queue`.
  5. Asynchronous consumer `flow-consume-milestone-notification` picks up message, logs dispatch, and marks outbox record `SENT`.

---

### Request 4: POST Out-of-Order Stale BlueDart Scan (Non-Regression)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `bluedart-webhook-secret-key-2026`
- **Body**:
  ```json
  {
    "awb_no": "BD-987654321",
    "status_code": "PU",
    "status_description": "Delayed pickup confirmation timestamp from earlier origin scan",
    "scan_date_time": "2026-10-10T08:00:00+05:30",
    "location_code": "BOM/FC",
    "location_name": "Mumbai FC Origin"
  }
  ```
- **Why this body is used**: Simulates a courier driver's handheld device syncing an old pickup scan (`PU`) from yesterday after the package has already progressed to `IN_TRANSIT`.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "OUT_OF_ORDER_RECORDED",
    "message": "Stale or out-of-order event recorded in audit history. Current shipment status preserved without regression.",
    "isDuplicate": false,
    "isOutOfOrder": true,
    "isPendingUnknown": false
  }
  ```
- **Internal System Actions**:
  1. State machine evaluates status rank: incoming `PICKED_UP` rank is `20`, current master rank is `30`.
  2. Incoming timestamp (`2026-10-10`) is older than current timestamp (`2026-10-11`).
  3. Out-of-Order detected (`vars.isOutOfOrder = true`).
  4. Master `shipments` table is **NOT** regressed. Current status remains `IN_TRANSIT`.
  5. Audit scan is safely recorded in `shipment_tracking_events` with `processing_result = 'OUT_OF_ORDER_RECORDED'`.

---

### Request 5: POST Unknown Shipment Scan (Quarantine Buffer)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/DELHIVERY`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `delhivery-webhook-secret-key-2026`
- **Body**:
  ```json
  {
    "waybill": "DELH-99887766",
    "Status": {
      "status": "In Transit",
      "statusCode": "IT",
      "statusDateTime": "2026-10-11 11:45:00",
      "instructions": "Package moving between freight hubs"
    },
    "Scans": [
      {
        "scanType": "Bag In",
        "scanDateTime": "2026-10-11 11:45:00",
        "scannedLocation": "GGN/HUB"
      }
    ],
    "ExpectedDeliveryDate": "2026-10-13T18:00:00Z"
  }
  ```
- **Why this body is used**: Tests what happens when carrier scans arrive before the order exists in the WMS (`DELH-99887766` does not exist in `shipments`).
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "QUARANTINED_PENDING_REGISTRATION",
    "message": "Shipment record not found in master database. Event safely quarantined for auto-reconciliation.",
    "isDuplicate": false,
    "isOutOfOrder": false,
    "isPendingUnknown": true
  }
  ```
- **Internal System Actions**:
  1. Lookup in `shipments` table returns 0 rows.
  2. Event is quarantined into `pending_tracking_events` with status `PENDING`.
  3. No error is thrown to the carrier; delivery is acknowledged safely.

---

### Request 6: POST Register Master Shipment (WMS Creation)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/shipments`
- **Headers**:
  - `Content-Type`: `application/json`
- **Body**:
  ```json
  {
    "shipmentId": "SHP-1006",
    "trackingNumber": "BD-445566778",
    "carrier": "BLUEDART",
    "originLocation": "Hyderabad E-commerce Park",
    "destinationLocation": "Chennai South Hub",
    "promisedDeliveryTime": "2026-10-16T18:00:00Z"
  }
  ```
- **Why this body is used**: Simulates a Warehouse Management System (WMS) creating a new parcel order with guaranteed customer SLA.
- **Expected Status**: `201 Created`
- **Expected Response**:
  ```json
  {
    "shipmentId": "SHP-1006",
    "trackingNumber": "BD-445566778",
    "carrier": "BLUEDART",
    "currentStatus": "LABEL_CREATED",
    "statusRank": 10,
    "riskLevel": "ON_TRACK"
  }
  ```

---

### Request 7: POST Reconcile Quarantined Events (Auto-Recovery Batch)
- **Folder**: `03 - Control Tower Operations & Telemetry`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/events/reconcile`
- **Headers**:
  - `Content-Type`: `application/json`
- **Body**: None
- **Why this body is used**: Triggers the batch reconciliation flow to find quarantined scans in `pending_tracking_events` whose tracking numbers have now been registered in `shipments`.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "reconciledCount": 1,
    "status": "RECONCILIATION_COMPLETED",
    "message": "Reconciliation cycle executed. Processed 1 quarantined events."
  }
  ```

---

### Request 8: GET Shipment by Tracking Number (Master State)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/shipments/BD-987654321`
- **Headers**: None
- **Body**: None
- **Why this request is used**: Fetches real-time single-pane-of-glass status for parcel `BD-987654321`.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "shipmentId": "SHP-1001",
    "trackingNumber": "BD-987654321",
    "carrier": "BLUEDART",
    "originLocation": "Mumbai Fulfillment Center",
    "destinationLocation": "Delhi Regional Hub",
    "currentStatus": "IN_TRANSIT",
    "statusRank": 30,
    "riskLevel": "ON_TRACK"
  }
  ```

---

### Request 9: GET Shipment Event History (Immutable Audit Trail)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/shipments/BD-987654321/history`
- **Headers**: None
- **Body**: None
- **Why this request is used**: Retrieves the complete chronological audit list of all physical scans received for this package.
- **Expected Status**: `200 OK`
- **Expected Response**: Array of JSON event objects showing original status, canonical status, scan timestamps, and processing results (`PROCESSED`, `OUT_OF_ORDER_RECORDED`).

---

### Request 10: GET Explainable Delay Risk Assessment (SLA Breach Engine)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/shipments/BD-123456789/risk`
- **Headers**: None
- **Body**: None
- **Why this request is used**: Evaluates why shipment `BD-123456789` is at risk of missing customer delivery promises.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "shipmentId": "SHP-1003",
    "trackingNumber": "BD-123456789",
    "carrier": "BLUEDART",
    "currentStatus": "IN_TRANSIT",
    "riskLevel": "DELAYED",
    "reasonCode": "PROMISED_SLA_BREACHED",
    "explanation": "Promised delivery deadline has passed. Current shipment status is IN_TRANSIT.",
    "riskFactors": [
      "Promised SLA: 2026-10-10 12:00:00",
      "Current time exceeds deadline",
      "Package still in transit"
    ]
  }
  ```

---

### Request 11: GET Customer Notification Messages (Transactional Outbox)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/shipments/DELH-11223344/notifications`  
  *(Or: `http://localhost:8081/api/v1/shipments/BD-987654321/notifications`)*
- **Headers**: None
- **Body**: None
- **Why this request is used**: Directly displays the customer-facing message generated by the Control Tower when a package hits a milestone (`OUT_FOR_DELIVERY`, `DELIVERED`, `PICKED_UP`, `EXCEPTION`).
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  [
    {
      "id": 1,
      "notificationId": "NOTIF-79b8a2e1",
      "shipmentId": "SHP-1002",
      "trackingNumber": "DELH-11223344",
      "carrier": "DELHIVERY",
      "milestone": "OUT_FOR_DELIVERY",
      "messageBody": "Out for delivery! Your package is with our delivery agent and will arrive today.",
      "channels": ["SMS", "EMAIL"],
      "status": "SENT",
      "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501",
      "createdAt": "2026-10-12T00:15:30Z",
      "sentAt": "2026-10-12T00:15:30Z"
    }
  ]
  ```
- **Internal System Actions**:
  1. Queries the MySQL `notification_outbox` table by tracking number or shipment ID.
  2. Returns the exact text message, notification status (`SENT`), channels, and timestamps sent out via the asynchronous VM queue.

---

### Request 12: GET Operational Health Check (Liveness Probe)
- **Folder**: `03 - Control Tower Operations & Telemetry`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/health`
- **Headers**: None
- **Body**: None
- **Why this request is used**: Validates that Mule runtime, MySQL connection pool (`SELECT 1`), and VM Queue are healthy.
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "status": "UP",
    "service": "Shipment Signal Control Tower API",
    "version": "1.0.0",
    "environment": "dev",
    "database": "CONNECTED",
    "queue": "CONNECTED"
  }
  ```

---

### Request 12: GET Carrier Pulse Telemetry (Control Tower Dashboard Metrics)
- **Folder**: `03 - Control Tower Operations & Telemetry`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/carriers/pulse`
- **Headers**: None
- **Body**: None
- **Why this request is used**: Powers the real-time operational dashboard with carrier-level metrics (total scans, duplicates suppressed, out-of-order scans caught, quarantined count).
- **Expected Status**: `200 OK`
- **Expected Response**:
  ```json
  [
    {
      "carrier": "BLUEDART",
      "totalEventsReceived": 3,
      "successfullyProcessed": 2,
      "duplicateEvents": 1,
      "outOfOrderEvents": 1,
      "healthStatus": "HEALTHY"
    },
    {
      "carrier": "DELHIVERY",
      "totalEventsReceived": 2,
      "successfullyProcessed": 1,
      "pendingUnknownShipments": 1,
      "healthStatus": "HEALTHY"
    }
  ]
  ```

---

### Request 13: POST Webhook Security Rejection – Invalid Token (401 Unauthorized)
- **Folder**: `04 - Negative Testing & Security`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `FORGED_UNAUTHORIZED_TOKEN`
- **Body**:
  ```json
  {
    "awb_no": "BD-987654321",
    "status_code": "IT"
  }
  ```
- **Why this request is used**: Demonstrates that unauthorized attackers cannot forge webhook events into the control tower.
- **Expected Status**: `401 Unauthorized`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "UNAUTHORIZED",
      "message": "Invalid or missing X-Carrier-Token header for carrier webhook."
    }
  }
  ```

---

### Request 14: POST Unsupported Carrier Code (400 Bad Request)
- **Folder**: `04 - Negative Testing & Security`
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/UNKNOWN_EXPRESS`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `bluedart-webhook-secret-key-2026`
- **Body**: `{ "tracking_number": "FDX-998877" }`
- **Why this request is used**: Proves input validation protects against un-onboarded 3PL partners.
- **Expected Status**: `400 Bad Request`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "UNSUPPORTED_CARRIER",
      "message": "Carrier UNKNOWN_EXPRESS is not currently onboarded to the system. Supported: BLUEDART, DELHIVERY"
    }
  }
  ```

---

### Request 15: GET Non-Existent Shipment (404 Not Found)
- **Folder**: `04 - Negative Testing & Security`
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/shipments/NON_EXISTENT_AWB_9999`
- **Headers**: None
- **Body**: None
- **Why this request is used**: Proves clean error handling with RFC-compliant error payloads.
- **Expected Status**: `404 Not Found`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "Shipment with identifier NON_EXISTENT_AWB_9999 does not exist in the system."
    }
  }
  ```

---

## 4. Step-by-Step Hackathon Presentation & Runbook (Start to End)

Follow this chronological execution script during your live Hackathon demonstration:

```
[Step 0: Pre-Flight Check]
Ensure MySQL is running, Mule app is started in Studio, and Postman Environment is selected.
   │
   ▼
[Step 1: System Baseline] ─────────► Execute GET /health & GET /carriers/pulse
   │                                  Show judges all subsystems are UP.
   ▼
[Step 2: Carrier Normalization] ───► Execute POST BlueDart In-Transit
   │                                  Show raw BlueDart payload converted to Canonical Model.
   ▼
[Step 3: Idempotency Proof] ───────► Click SEND again on BlueDart In-Transit
   │                                  Show DUPLICATE_ACKNOWLEDGED, isDuplicate: true & WARN log.
   ▼
[Step 4: Non-Regression Check] ────► Execute POST Out-of-Order Stale BlueDart
   │                                  Show status stays IN_TRANSIT, does NOT regress to PICKED_UP.
   ▼
[Step 5: Milestone Alert] ─────────► Execute POST Delhivery Out-for-Delivery
   │                                  Show Transactional Outbox row and VM Queue alert dispatch.
   ▼
[Step 6: Quarantine & Reconcile] ──► Execute POST Unknown Scan -> GET Quarantine -> POST Reconcile
   │                                  Show zero data loss when scans arrive before WMS orders.
   ▼
[Step 7: Explainable Risk Engine] ─► Execute GET /shipments/BD-123456789/risk
   │                                  Show automated calculation of DELAYED risk & breach reasons.
   ▼
[Step 8: Security Defense] ────────► Execute POST with Invalid Token
                                      Show instant HTTP 401 Unauthorized rejection.
```

### Detailed Minute-by-Minute Execution Guide

#### Step 0: Pre-Flight Setup (Before Judges Arrive)
1. In MySQL Workbench, execute `sample-data.sql` to clean and reseed master records.
2. In Anypoint Studio, verify the console displays:  
   `**********************************************************************`  
   `* Application: shipment-signal-control-tower                       *`  
   `* OS encoding: UTF-8, Mule encoding: UTF-8                           *`  
   `* Status: DEPLOYED                                                  *`  
   `**********************************************************************`
3. In Postman, select environment **Shipment Tracking - Local Environment**.

---

#### Step 1: Health & Baseline Telemetry (Minute 0:00 – 1:00)
- **Postman Action**: Run `GET {{baseUrl}}/health`
- **What to Say to Judges**:  
  *"We begin by verifying our control tower architecture. Our health probe confirms the Mule 4 runtime, MySQL connection pool, and asynchronous VM queues are all active and connected."*
- **Postman Action**: Run `GET {{baseUrl}}/carriers/pulse`
- **What to Say to Judges**:  
  *"Our Carrier Pulse API aggregates real-time telemetry across all 3PL carriers, tracking total volume, duplicates suppressed, and out-of-order scans caught."*

---

#### Step 2: BlueDart Normalization & State Progression (Minute 1:00 – 2:15)
- **Postman Action**: Run `POST {{baseUrl}}/webhooks/carriers/BLUEDART` (In-Transit Scan)
- **What to Say to Judges**:  
  *"Here is BlueDart's proprietary payload with `awb_no: BD-987654321`, carrier code `status_code: 'IT'`, and local IST timestamp. Notice our security header `X-Carrier-Token`."*
- **Click**: **Send**
- **Show Judges**:
  - Response returns `200 OK` in `< 30ms`.
  - Canonical status normalized to `"IN_TRANSIT"`.
  - In MySQL Workbench, run:
    ```sql
    SELECT tracking_number, current_status, status_rank, risk_level 
    FROM shipments WHERE tracking_number = 'BD-987654321';
    ```
    Status has progressed from `LABEL_CREATED` to `IN_TRANSIT` with rank `30`.

---

#### Step 3: Idempotency & Duplicate Suppression (Minute 2:15 – 3:30)
- **Postman Action**: Run `POST Duplicate BlueDart Scan (Idempotency Test)` (or simply hit **Send** again on Request 1)
- **What to Say to Judges**:  
  *"In real logistics, carrier webhooks retry upon network hiccups. We now send the exact same scan a second time."*
- **Click**: **Send**
- **Show Judges**:
  - API response returns `status: "DUPLICATE_ACKNOWLEDGED"`, `"isDuplicate": true`.
  - In Studio Console, show the warning log:  
    `WARN ... [Idempotency] Duplicate event detected and suppressed. EventKey: BLUEDART-BD-987654321-IT-...`
  - In MySQL, show that `shipment_tracking_events` still has **only 1 row**, and **zero duplicate customer messages** were generated.

---

#### Step 4: Out-of-Order Stale Scan Handling (Minute 3:30 – 4:30)
- **Postman Action**: Run `POST Out-of-Order Stale BlueDart Scan`
- **What to Say to Judges**:  
  *"Now we test out-of-order delivery. A driver's handheld syncs an older pickup scan (`PU`) from earlier in the morning for package `BD-987654321`. In simple architectures, the status regresses backwards. Watch how our state machine handles it."*
- **Click**: **Send**
- **Show Judges**:
  - API response returns `status: "OUT_OF_ORDER_RECORDED"`, `"isOutOfOrder": true`.
  - In MySQL, run `SELECT current_status FROM shipments WHERE tracking_number = 'BD-987654321';`.
  - Master status remains **`IN_TRANSIT`**! It did **not** regress to `PICKED_UP`.
  - The audit row is safely recorded in `shipment_tracking_events` for audit history.

---

#### Step 5: Delhivery Milestone & Transactional Outbox (Minute 4:30 – 5:30)
- **Postman Action**: Run `POST Delhivery Webhook - Out for Delivery Scan`
- **What to Say to Judges**:  
  *"Now observe Delhivery's completely different nested structure with `waybill` and `Status.statusCode: 'OFD'`. Because `OUT_FOR_DELIVERY` is a critical milestone, our transactional outbox triggers a customer notification."*
- **Click**: **Send**
- **Show Judges**:
  - Status normalized to `"OUT_FOR_DELIVERY"`.
  - In MySQL, run:
    ```sql
    SELECT notification_id, tracking_number, milestone, status, sent_at 
    FROM notification_outbox;
    ```
    Alert is recorded with status `SENT`.
  - In Studio Console, show the async consumer log:  
    `[Notification Consumer - Dispatched Alert] >>> NOTIFICATION DELIVERED >>> NotificationId: NOTIF-... | Milestone: OUT_FOR_DELIVERY`

---

#### Step 6: Quarantine Buffer & Batch Auto-Reconciliation (Minute 5:30 – 6:30)
- **Postman Action**: Run `POST Unknown Shipment Scan (Quarantine Buffer)`
- **What to Say to Judges**:  
  *"A carrier scans package `DELH-99887766` which has not yet been registered in our WMS. Instead of dropping the event or throwing an error, we quarantine it."*
- **Click**: **Send**
- **Show Judges**:
  - Response returns `status: "QUARANTINED_PENDING_REGISTRATION"`, `"isPendingUnknown": true`.
  - In MySQL, show the row in `pending_tracking_events`.
- **Postman Action**: Run `POST Reconcile Quarantined Events Batch`
- **Click**: **Send**
- **Show Judges**:
  - Returns `reconciledCount: 1`, `status: "RECONCILIATION_COMPLETED"`. The scan has been automatically retrieved from quarantine and processed into the active tracking history.

---

#### Step 7: Explainable Delay Risk Assessment (Minute 6:30 – 7:30)
- **Postman Action**: Run `GET Explainable Risk Assessment (Delayed SLA)`
- **What to Say to Judges**:  
  *"Our risk engine proactively predicts SLA breaches. For shipment `BD-123456789`, the promised delivery time was yesterday, but the parcel is still in transit."*
- **Click**: **Send**
- **Show Judges**:
  - Returns `riskLevel: "DELAYED"`.
  - Returns clear explanation: `"Promised delivery deadline has passed. Current shipment status is IN_TRANSIT."`
  - Returns exact risk factors list.

---

#### Step 8: Security & Negative Testing Defense (Minute 7:30 – 8:00)
- **Postman Action**: Run `POST Webhook - Missing / Invalid Auth Token (401)`
- **What to Say to Judges**:  
  *"Finally, our security defense. When an attacker passes an invalid token, our policy immediately blocks the request with HTTP 401 Unauthorized before any downstream processing."*
- **Click**: **Send**
- **Show Judges**: Returns `401 Unauthorized` with structured error message.

---

### Summary Checklist for Demo Day
| # | Demo Action | Target Component | Key Takeaway for Judges |
|---|---|---|---|
| 1 | `GET /health` | System Health | Enterprise readiness, connection pooling |
| 2 | `POST /webhooks/carriers/BLUEDART` | DataWeave Normalizer | Heterogeneous payload translation into Canonical Model |
| 3 | `POST Duplicate BlueDart Scan` | Idempotency Engine | Exact duplicate detection, zero redundant DB writes or alerts |
| 4 | `POST Stale BlueDart Scan` | State Machine | Forward-only status rank progression, no state downgrade |
| 5 | `POST Delhivery OFD Scan` | Outbox + VM Queue | Reliable async decoupled customer milestone notifications |
| 6 | `POST Unknown Scan` + `Reconcile` | Quarantine Buffer | Zero data loss for out-of-sequence order registration |
| 7 | `GET .../risk` | Explainable Risk Engine | Proactive SLA breach calculation with transparent explanation |
| 8 | `POST Invalid Token` | Security Gateway | Token-based webhook authentication rejection |
