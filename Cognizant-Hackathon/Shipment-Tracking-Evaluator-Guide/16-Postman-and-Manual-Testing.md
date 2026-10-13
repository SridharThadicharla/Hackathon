# 16 – Postman Collection & Live Manual Testing Guide

**Collection File**: `postman/Shipment-Tracking.postman_collection.json`  
**Environment File**: `postman/local-environment.postman_environment.json`  
**Default Base URL**: `http://localhost:8081/api/v1`  
**Total Requests**: 16 Requests across 4 Functional Folders  

---

## 1. Importing the Collection & Environment in Postman

1. Open the **Postman Desktop Application**.
2. Click the **Import** button in the top-left corner.
3. Drag and drop both JSON files from `Cognizant-Hackathon/Shipment-Signal-Control-Tower/postman/`:
   - `Shipment-Tracking.postman_collection.json`
   - `local-environment.postman_environment.json`
4. In the top-right environment dropdown, select:
   **Shipment Tracking - Local Environment**.
5. Verify the pre-configured variables:
   - `baseUrl`: `http://localhost:8081/api/v1`
   - `bluedartToken`: `bluedart-webhook-secret-key-2026`
   - `delhiveryToken`: `delhivery-webhook-secret-key-2026`
   - `trackingNumberBlueDart`: `BD-987654321`
   - `trackingNumberDelhivery`: `DELH-11223344`
   - `trackingNumberDelayed`: `BD-123456789`
   - `trackingNumberUnknown`: `DELH-99887766`

---

## 2. Comprehensive Request Catalog by Folder

### Folder 01: Carrier Webhook Ingestion

#### Request 1: POST BlueDart Webhook – In Transit Scan
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
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "EVENT_PROCESSED_SUCCESSFULLY"`, `"normalizedStatus": "IN_TRANSIT"`.
- **Database Effect**: `shipments.current_status` updates to `IN_TRANSIT` (Rank 30). Audit row inserted into `shipment_tracking_events`.
- **Notification Effect**: Suppressed (internal hub scan).

---

#### Request 2: POST Delhivery Webhook – Out for Delivery Scan
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
      "statusDateTime": "2026-10-12 08:30:00",
      "instructions": "Package out for delivery with courier agent Ram"
    },
    "Scans": [
      {
        "scanType": "Van Out",
        "scanDateTime": "2026-10-12 08:30:00",
        "scannedLocation": "HYD/BEGUMPET"
      }
    ],
    "ExpectedDeliveryDate": "2026-10-12T18:00:00Z"
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "EVENT_PROCESSED_SUCCESSFULLY"`, `"normalizedStatus": "OUT_FOR_DELIVERY"`.
- **Database Effect**: `shipments.current_status` updates to `OUT_FOR_DELIVERY` (Rank 40). Outbox row created in `notification_outbox`.
- **Queue & Email Effect**: Enqueued in `shipment-milestone-queue`, consumed asynchronously, marked `SENT`.

---

#### Request 3: POST Duplicate BlueDart Scan (Idempotency Test)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Body**: Identical to Request 1.
- **Expected Status**: `200 OK`
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
- **Verification**: Zero duplicate rows in `shipment_tracking_events`. Outbox is suppressed.

---

#### Request 4: POST Out-of-Order Stale BlueDart Scan (Anti-Regression)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Body**: Stale pickup scan with timestamp `"2026-10-10T08:00:00+05:30"` for a shipment already at `IN_TRANSIT`.
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "OUT_OF_ORDER_RECORDED"`, `"isOutOfOrder": true`.
- **Database Verification**: `shipments.current_status` remains `IN_TRANSIT` (does NOT regress to `PICKED_UP`). Audit row recorded with `processing_result = 'OUT_OF_ORDER_RECORDED'`.

---

#### Request 5: POST Unknown Shipment Scan (Quarantine Buffer)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/DELHIVERY`
- **Body**: Scan for waybill `DELH-99887766` (unmanifested).
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "QUARANTINED_PENDING_REGISTRATION"`, `"isPendingUnknown": true`.
- **Database Verification**: Record saved in `pending_tracking_events` with `processing_status = 'PENDING'`.

---

### Folder 02: Shipment Management & Tracking

#### Request 6: POST Register Shipment (WMS Master Creation)
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
- **Expected Status**: `201 Created`
- **Response**: Full `ShipmentDetail` object with `currentStatus: "LABEL_CREATED"`.

---

#### Request 7: GET Shipment By Tracking Number
- **Method & URL**: `GET {{baseUrl}}/shipments/{{trackingNumberBlueDart}}`
- **Expected Status**: `200 OK`
- **Response**: Current master state, status rank, and risk level.

---

#### Request 8: GET Shipment Event History (Audit Trail)
- **Method & URL**: `GET {{baseUrl}}/shipments/{{trackingNumberBlueDart}}/history`
- **Expected Status**: `200 OK`
- **Response**: Chronological array of all physical and canonical events.

---

#### Request 9: GET Explainable Risk Assessment (Delayed SLA)
- **Method & URL**: `GET {{baseUrl}}/shipments/{{trackingNumberDelayed}}/risk`
- **Expected Status**: `200 OK`
- **Response**:
  ```json
  {
    "shipmentId": "SHP-1003",
    "trackingNumber": "BD-123456789",
    "carrier": "BLUEDART",
    "currentStatus": "IN_TRANSIT",
    "riskLevel": "DELAYED",
    "reasonCode": "PROMISED_SLA_BREACHED",
    "explanation": "Promised customer delivery date has elapsed while package remains in transit."
  }
  ```

---

#### Request 10: GET Customer Notification Messages (Transactional Outbox)
- **Method & URL**: `GET {{baseUrl}}/shipments/{{trackingNumberDelhivery}}/notifications`
- **Expected Status**: `200 OK`
- **Response**: Array of all dispatched customer milestone alerts with `status: "SENT"`.

---

### Folder 03: Control Tower Telemetry & Health

#### Request 11: GET Operational Health Check
- **Method & URL**: `GET {{baseUrl}}/health`
- **Expected Status**: `200 OK`
- **Response**: `"database": "CONNECTED"`, `"queue": "CONNECTED"`, `"status": "UP"`.

---

#### Request 12: GET Carrier Pulse Metrics & Telemetry
- **Method & URL**: `GET {{baseUrl}}/carriers/pulse`
- **Expected Status**: `200 OK`
- **Response**: Array summarizing total events, processed counts, duplicates, and out-of-order counts per courier partner.

---

#### Request 13: POST Reconcile Quarantined Events Batch
- **Method & URL**: `POST {{baseUrl}}/events/reconcile`
- **Expected Status**: `200 OK`
- **Response**: Reprocesses all quarantined pending events for newly registered parcels, returning `"reconciledCount"`.

---

### Folder 04: Negative Testing & Security Validation (All 15 Scenarios)

#### Request 14: N01 - Missing / Invalid Carrier Token (401 Unauthorized)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `INVALID_TOKEN_SECRET_999`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "awb_no": "{{trackingNumberBlueDart}}",
    "status_code": "IT",
    "status_description": "Unauthorized ingress scan attempt"
  }
  ```
- **Expected Status**: `401 Unauthorized`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "UNAUTHORIZED",
      "message": "Invalid or missing X-Carrier-Token header for carrier webhook."
    },
    "correlationId": "{{correlationId}}"
  }
  ```
- **System Behavior**: Request rejected immediately; zero database writes and zero notifications.

---

#### Request 15: N01-B - Completely Missing Token Header (401 Unauthorized)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/DELHIVERY`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Correlation-ID`: `{{correlationId}}`
  *(Note: `X-Carrier-Token` header omitted entirely)*
- **Body**:
  ```json
  {
    "waybill": "{{trackingNumberDelhivery}}",
    "Status": { "statusCode": "OFD", "status": "Out for Delivery" }
  }
  ```
- **Expected Status**: `401 Unauthorized`
- **Expected Response**: `"error": { "code": "UNAUTHORIZED" }`

---

#### Request 16: N02-A - Malformed Payload - Missing Tracking Number AWB (400 Bad Request)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "status_code": "IT",
    "status_description": "In Transit scan missing mandatory awb_no",
    "scan_date_time": "2026-10-13T10:00:00+05:30"
  }
  ```
- **Expected Status**: `400 Bad Request`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "BAD_REQUEST",
      "message": "BlueDart payload is missing required tracking number (awb_no) or status_code."
    },
    "correlationId": "{{correlationId}}"
  }
  ```

---

#### Request 17: N02-B - Malformed Payload - Missing Carrier Status (400 Bad Request)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/DELHIVERY`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{delhiveryToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "waybill": "{{trackingNumberDelhivery}}"
  }
  ```
- **Expected Status**: `400 Bad Request`
- **Expected Response**: `"code": "BAD_REQUEST"`, `"message": "Delhivery payload is missing required tracking number (waybill) or status."`

---

#### Request 18: N02-C - Malformed Syntax - Broken JSON (400 Bad Request)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
- **Body** (raw text with broken syntax):
  ```
  {
    "awb_no": "BD-987654321",
    "status_code": 
  ```
- **Expected Status**: `400 Bad Request`
- **Expected Response**: `"code": "BAD_REQUEST"`, `"message": "Invalid request payload or malformed syntax."`

---

#### Request 19: N03 - Unsupported Carrier Code (400 Bad Request)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/FEDEX`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "tracking_number": "FEDEX-11223344",
    "status": "IN_TRANSIT"
  }
  ```
- **Expected Status**: `400 Bad Request`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "UNSUPPORTED_CARRIER",
      "message": "Carrier code 'FEDEX' is not supported. Supported carriers: BLUEDART, DELHIVERY"
    }
  }
  ```

---

#### Request 20: N04 - Unmapped Carrier Status (200 Normalized to EXCEPTION & Alert)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "awb_no": "{{trackingNumberBlueDart}}",
    "status_code": "CUSTOMS_SPECIAL_HOLD",
    "status_description": "Shipment detained for regulatory verification",
    "scan_date_time": "2026-10-13T11:00:00+05:30",
    "location_code": "BOM/AIRPORT",
    "location_name": "Mumbai Air Cargo Complex"
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: `"normalizedStatus": "EXCEPTION"`, `"originalStatus": "CUSTOMS_SPECIAL_HOLD"`.
- **Side Effect**: New row in `integration_alerts` with `alert_type = 'UNKNOWN_STATUS'`.

---

#### Request 21: N05 - Unknown Tracking Number (200 Quarantined to Pending Buffer)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/DELHIVERY`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{delhiveryToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "waybill": "DELH-NOT-YET-REGISTERED-8888",
    "Status": {
      "status": "In Transit",
      "statusCode": "IT",
      "statusDateTime": "2026-10-13 11:30:00"
    },
    "Scans": [{ "scannedLocation": "GGN/HUB", "scanDateTime": "2026-10-13 11:30:00" }]
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "QUARANTINED_PENDING_REGISTRATION"`, `"isPendingUnknown": true`.
- **Database Effect**: Inserted into `pending_tracking_events` table for auto-reconciliation.

---

#### Request 22: N06 - Duplicate Webhook Delivery (200 Suppressed & Idempotent)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**: Identical payload and timestamp as an existing scan.
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "DUPLICATE_ACKNOWLEDGED"`, `"isDuplicate": true`.
- **Side Effect**: Zero new rows in `shipment_tracking_events`, zero emails dispatched.

---

#### Request 23: N07 - Out-of-Order Stale Scan (200 No Current Status Regression)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "awb_no": "{{trackingNumberBlueDart}}",
    "status_code": "PU",
    "status_description": "Delayed pickup scan arriving after in-transit hops",
    "scan_date_time": "2026-10-10T08:00:00+05:30"
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "OUT_OF_ORDER_RECORDED"`, `"isOutOfOrder": true`.
- **Database Effect**: Audit history row saved, but `shipments.current_status` remains `OUT_FOR_DELIVERY` without regressing.

---

#### Request 24: N08 - Transit Scan After Delivery (200 Preserves Delivered State)
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
      "statusCode": "IT",
      "status": "Delayed transit scan arriving after package delivered"
    },
    "Scans": [{ "scannedLocation": "BOM/SORT", "scanDateTime": "2026-10-13 15:00:00" }]
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "OUT_OF_ORDER_RECORDED"`, `"isOutOfOrder": true`.
- **State Effect**: Terminal `DELIVERED` status preserved.

---

#### Request 25: N12 - Internal Hub Scan Milestone Filter (200 Suppresses Customer Email)
- **Method & URL**: `POST {{baseUrl}}/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Carrier-Token`: `{{bluedartToken}}`
  - `X-Correlation-ID`: `{{correlationId}}`
- **Body**:
  ```json
  {
    "awb_no": "{{trackingNumberBlueDart}}",
    "status_code": "AR",
    "status_description": "Arrived at intermediate sorting hub",
    "scan_date_time": "2026-10-13T13:00:00+05:30",
    "location_code": "NAG/HUB",
    "location_name": "Nagpur Transit Center"
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: `"status": "EVENT_PROCESSED_SUCCESSFULLY"`, `"customerNotification": null`.
- **Notification Effect**: Customer email suppressed (internal hop).

---

#### Request 26: N14 - Malformed Timestamp String Fallback (200 Safe Resilient Parsing)
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
    "status_description": "Scan with non-standard datetime string",
    "scan_date_time": "CORRUPTED_NON_ISO_TIMESTAMP_XYZ"
  }
  ```
- **Expected Status**: `200 OK`
- **Expected Response**: Event normalized safely using current UTC fallback without crashing.

---

#### Request 27: GET Shipment – Non-Existent Identifier (404 Not Found)
- **Method & URL**: `GET {{baseUrl}}/shipments/NON_EXISTENT_AWB_9999`
- **Headers**: (None required)
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

#### Request 28: DELETE Shipment – Method Not Allowed (405 Method Not Allowed)
- **Method & URL**: `DELETE {{baseUrl}}/shipments/{{trackingNumberBlueDart}}`
- **Expected Status**: `405 Method Not Allowed`
- **Expected Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "METHOD_NOT_ALLOWED",
      "message": "HTTP method is not allowed for this endpoint."
    }
  }
  ```

