# 10 – Postman Complete Testing Guide

**Project**: Shipment Signal Control Tower  
**Collection File**: `postman/Shipment-Tracking.postman_collection.json`  
**Environment File**: `postman/local-environment.postman_environment.json`  
**Default Base URL**: `http://localhost:8081/api/v1`  

---

## 1. Importing Collection & Environment in Postman

1. Open the **Postman Desktop Application**.
2. In the top-left corner, click **Import**.
3. Drag and drop both JSON files from `Cognizant-Hackathon/Shipment-Signal-Control-Tower/postman/`:
   - `Shipment-Tracking.postman_collection.json`
   - `local-environment.postman_environment.json`
4. In the top-right environment selector dropdown, select **Shipment Tracking - Local Environment**.
5. Verify the environment variables:
   - `baseUrl`: `http://localhost:8081/api/v1`
   - `bluedartToken`: `bluedart-webhook-secret-key-2026`
   - `delhiveryToken`: `delhivery-webhook-secret-key-2026`
   - `trackingNumberBlueDart`: `BD-987654321`
   - `trackingNumberDelhivery`: `DELH-11223344`
   - `trackingNumberDelayed`: `BD-123456789`
   - `trackingNumberUnknown`: `DELH-99887766`

---

## 2. Complete Request Catalog & Execution Scenarios

---

### Request 1: POST BlueDart Webhook – In Transit Scan
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "awb_no": "{{trackingNumberBlueDart}}",
    "status_code": "IT",
    "status_description": "In Transit - Forwarded to Destination Hub",
    "scan_date_time": "2026-10-11T10:30:00+05:30",
    "location_code": "DEL/HUB",
    "location_name": "Delhi Regional Sorting Hub",
    "eta": "2026-10-14T18:00:00+05:30"
  }
  ```
- **Expected HTTP Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "EVENT_PROCESSED_SUCCESSFULLY",
    "message": "Shipment event received, normalized, persisted, and evaluated.",
    "shipmentId": "SHP-1001",
    "trackingNumber": "BD-987654321",
    "carrier": "BLUEDART",
    "normalizedStatus": "IN_TRANSIT",
    "isDuplicate": false,
    "isOutOfOrder": false,
    "isPendingUnknown": false
  }
  ```
- **Expected Database Changes**:
  - `shipments`: `current_status` updated to `IN_TRANSIT`, `status_rank` = `30`, `risk_level` = `ON_TRACK`.
  - `shipment_tracking_events`: New audit row inserted with `processing_result = 'PROCESSED'`.
- **Expected Queue Behavior**: Event is a transit scan; customer notification suppressed (only milestone scans notify).

---

### Request 2: POST Delhivery Webhook – Out for Delivery Scan
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/DELHIVERY`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{delhiveryToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "waybill": "{{trackingNumberDelhivery}}",
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
- **Expected HTTP Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "EVENT_PROCESSED_SUCCESSFULLY",
    "normalizedStatus": "OUT_FOR_DELIVERY"
  }
  ```
- **Expected Database & Queue Behavior**:
  - `shipments`: `current_status` updated to `OUT_FOR_DELIVERY` (`status_rank` = `40`).
  - `notification_outbox`: Outbox entry created with `milestone = 'OUT_FOR_DELIVERY'`.
  - `VM Queue`: Alert enqueued and consumed by `flow-consume-milestone-notification`, updating outbox status to `SENT`.

---

### Request 3: POST Duplicate BlueDart Scan (Idempotency Test)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Body**: Exact same body as Request 1.
- **Expected HTTP Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "DUPLICATE_ACKNOWLEDGED",
    "message": "Event already processed and recorded. Duplicate delivery suppressed safely.",
    "isDuplicate": true,
    "isOutOfOrder": false
  }
  ```
- **Expected Database Verification**: Zero duplicate rows in `shipment_tracking_events`. Outbox is suppressed.

---

### Request 4: POST Out-of-Order Stale BlueDart Scan
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Body**: Stale origin pickup scan with timestamp `'2026-10-10T08:00:00+05:30'` (older than current status timestamp).
- **Expected HTTP Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "OUT_OF_ORDER_RECORDED",
    "message": "Stale or out-of-order event recorded in audit history. Current shipment status preserved without regression.",
    "isOutOfOrder": true
  }
  ```
- **Expected Database Verification**:
  - `shipments`: `current_status` remains `IN_TRANSIT` (NO regression to `PICKED_UP`).
  - `shipment_tracking_events`: Recorded with `processing_result = 'OUT_OF_ORDER_RECORDED'`.

---

### Request 5: POST Unknown Shipment Scan (Quarantine Buffer)
- **Folder**: `01 - Webhooks - Carrier Ingestion`
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/DELHIVERY`
- **Body**: Scan for `DELH-99887766` (which does not exist in `shipments` master table yet).
- **Expected HTTP Status**: `200 OK`
- **Expected Response**:
  ```json
  {
    "success": true,
    "status": "QUARANTINED_PENDING_REGISTRATION",
    "message": "Shipment record not found in master database. Event safely quarantined for auto-reconciliation.",
    "isPendingUnknown": true
  }
  ```
- **Expected Database Verification**: Quarantined into `pending_tracking_events` with `processing_status = 'PENDING'`.

---

### Request 6: POST Register Shipment (WMS Master Creation)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method & URL**: `POST {{baseUrl}}/shipments`
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
- **Expected HTTP Status**: `201 Created`

---

### Request 7: GET Shipment By Tracking Number
- **Folder**: `02 - Shipment Management & Tracking`
- **Method & URL**: `GET {{baseUrl}}/shipments/BD-987654321`
- **Expected HTTP Status**: `200 OK`
- **Response**: Full `ShipmentDetail` JSON with `currentStatus: "IN_TRANSIT"` and `riskLevel: "ON_TRACK"`.

---

### Request 8: GET Shipment Event History
- **Folder**: `02 - Shipment Management & Tracking`
- **Method & URL**: `GET {{baseUrl}}/shipments/BD-987654321/history`
- **Expected HTTP Status**: `200 OK`
- **Response**: JSON array showing all chronological scans for `BD-987654321`.

---

### Request 9: GET Explainable Risk Assessment (Delayed SLA)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method & URL**: `GET {{baseUrl}}/shipments/BD-123456789/risk`
- **Expected HTTP Status**: `200 OK`
- **Response**:
  ```json
  {
    "shipmentId": "SHP-1003",
    "trackingNumber": "BD-123456789",
    "currentStatus": "IN_TRANSIT",
    "riskLevel": "DELAYED",
    "reasonCode": "PROMISED_SLA_BREACHED",
    "explanation": "Promised delivery deadline has passed. Current shipment status is IN_TRANSIT."
  }
  ```

---

### Request 10: GET Customer Notification Messages (Transactional Outbox)
- **Folder**: `02 - Shipment Management & Tracking`
- **Method & URL**: `GET {{baseUrl}}/shipments/DELH-11223344/notifications`
- **Expected HTTP Status**: `200 OK`
- **Response**:
  ```json
  [
    {
      "id": 1,
      "notificationId": "NOTIF-c85d8984",
      "shipmentId": "SHP-1002",
      "trackingNumber": "DELH-11223344",
      "carrier": "DELHIVERY",
      "milestone": "OUT_FOR_DELIVERY",
      "messageBody": "Out for delivery! Your package is with our delivery agent and will arrive today.",
      "channels": ["SMS", "EMAIL"],
      "status": "SENT",
      "createdAt": "2026-10-12T00:15:30Z",
      "sentAt": "2026-10-12T00:15:30Z"
    }
  ]
  ```
- **Explanation**: Returns all customer alerts generated by the control tower for milestones (`OUT_FOR_DELIVERY`, `DELIVERED`, `PICKED_UP`, `EXCEPTION`).

---

### Request 11: GET Operational Health Check
- **Folder**: `03 - Control Tower Operations & Telemetry`
- **Method & URL**: `GET {{baseUrl}}/health`
- **Expected HTTP Status**: `200 OK`
- **Response**: `{ "status": "UP", "database": "CONNECTED", "queue": "CONNECTED" }`.

---

### Request 12: GET Carrier Pulse Metrics
- **Folder**: `03 - Control Tower Operations & Telemetry`
- **Method & URL**: `GET {{baseUrl}}/carriers/pulse`
- **Expected HTTP Status**: `200 OK`
- **Response**: Telemetry array containing totals for `BLUEDART` and `DELHIVERY`.

---

### Request 13: POST Reconcile Quarantined Events
- **Folder**: `03 - Control Tower Operations & Telemetry`
- **Method & URL**: `POST {{baseUrl}}/events/reconcile`
- **Expected HTTP Status**: `200 OK`
- **Response**: `{ "success": true, "reconciledCount": 1, "status": "RECONCILIATION_COMPLETED" }`.

---

### Request 14 to 16: Negative Tests
14. **POST Unauthorized Webhook** (Wrong Token): Returns `401 Unauthorized`.
15. **POST Unsupported Carrier Code**: Returns `400 Bad Request` with `UNSUPPORTED_CARRIER`.
16. **GET Non-Existent Shipment**: Returns `404 Not Found` with `RESOURCE_NOT_FOUND`.
