# 16 – Hackathon Live Demonstration Guide (7–9 Minute Script)

**Project**: Shipment Signal Control Tower  
**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  
**Target Audience**: Technical Judges, Architecture Panel, Solution Evaluators  

---

## 1. Pre-Demo Setup & Environment Readiness

Before starting your presentation, ensure these 3 windows are open and arranged on your screen:
1. **Left Half**: Postman Desktop Client (Collection: `Shipment Signal Control Tower`).
2. **Top-Right**: Anypoint Studio (Console log view active with Mule application running).
3. **Bottom-Right**: MySQL Workbench (Connected to `shipment_control_tower` with verification queries tab open).

---

## 2. Minute-by-Minute Demonstration Script

---

### Minute 0:00 – 1:00: Problem & Architecture Pitch
- **What to Say**:  
  *"Good morning judges. Today, e-commerce retailers and shippers rely on multiple 3PL carriers like BlueDart and Delhivery. Each carrier pushes tracking events in disparate, incompatible formats. Worse, network drops cause duplicate scans, drivers upload out-of-order scans, and packages are scanned before WMS orders are created.  
  We built the **Shipment Signal Control Tower** on Mule 4. It normalizes multi-carrier webhooks into a unified Canonical Event Model, enforces strict idempotency, prevents status downgrades, calculates explainable SLA delay risks, and guarantees notification delivery via a Transactional Outbox."*
- **What to Show**: Briefly display the 3-tier architecture diagram from `04-Architecture-and-API-Led-Connectivity.md`.

---

### Minute 1:00 – 2:15: Demo 1 – BlueDart Webhook & Canonical Normalization
- **Action in Postman**: Open folder `01 - Webhooks - Carrier Ingestion`, select:  
  **`POST BlueDart Webhook - In Transit Scan`**
- **Endpoint**: `POST http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`
- **What to Explain**:  
  *"Notice the incoming payload has BlueDart's proprietary format: `awb_no`, `status_code: 'IT'`, and local IST timestamp `+05:30`. Notice also our security header `X-Carrier-Token`."*
- **Click**: **Send**
- **Judge Observation**:  
  - Postman returns `200 OK` in `< 30ms`.
  - Response shows `normalizedStatus: "IN_TRANSIT"` and deterministic event key `BLUEDART-BD-987654321-IT-...`.
- **Action in MySQL Workbench**: Run query:  
  `SELECT tracking_number, current_status, status_rank, risk_level FROM shipments WHERE tracking_number = 'BD-987654321';`
- **Judge Observation**: Master shipment updated from `LABEL_CREATED` to `IN_TRANSIT` with rank `30` and `risk_level: 'ON_TRACK'`.

---

### Minute 2:15 – 3:30: Demo 2 – Delhivery Webhook & Milestone Notification Trigger
- **Action in Postman**: Select:  
  **`POST Delhivery Webhook - Out for Delivery Scan`**
- **Endpoint**: `POST http://localhost:8081/api/v1/webhooks/carriers/DELHIVERY`
- **What to Explain**:  
  *"Now observe Delhivery's completely different nested JSON structure with `waybill`, nested `Status.statusCode: 'OFD'`, and `Scans` array. When this package goes `OUT_FOR_DELIVERY`, it represents a critical customer milestone."*
- **Click**: **Send**
- **Judge Observation**:  
  - Postman returns `200 OK` with `normalizedStatus: "OUT_FOR_DELIVERY"`.
- **Action in Studio Console & MySQL Workbench**: Show:  
  `SELECT notification_id, tracking_number, milestone, status, sent_at FROM notification_outbox;`
- **Judge Observation**:  
  - The Transactional Outbox table recorded the alert with status `SENT`.
  - In Studio Console, show the asynchronous consumer log:  
    `[Notification Consumer - Dispatched Alert] >>> NOTIFICATION DELIVERED >>> NotificationId: NOTIF-... | Milestone: OUT_FOR_DELIVERY | Message: "Out for delivery! Your package is with our delivery agent and will arrive today."`

---

### Minute 3:30 – 4:30: Demo 3 – Idempotency & Duplicate Event Suppression
- **Action in Postman**: Re-select:  
  **`POST Duplicate BlueDart Scan (Idempotency Test)`**
- **What to Explain**:  
  *"Now we simulate a network retry where BlueDart pushes the exact same in-transit scan a second time."*
- **Click**: **Send**
- **Judge Observation**:  
  - Returns HTTP 200 with `status: "DUPLICATE_ACKNOWLEDGED"`, `isDuplicate: true`.
  - In MySQL, show that zero duplicate rows were added to `shipment_tracking_events`, and zero duplicate customer notifications were queued.

---

### Minute 4:30 – 5:30: Demo 4 – Out-of-Order Stale Scan (Forward-Only Progression)
- **Action in Postman**: Select:  
  **`POST Out-of-Order Stale BlueDart Scan`**
- **What to Explain**:  
  *"Here, a driver's handheld syncs a stale pickup scan (`PU`) from earlier in the morning for package `BD-987654321`, which is ALREADY in `IN_TRANSIT`. In naive systems, the status regresses backwards. Watch how our state machine handles it."*
- **Click**: **Send**
- **Judge Observation**:  
  - Response returns `status: "OUT_OF_ORDER_RECORDED"`, `isOutOfOrder: true`.
  - In MySQL, run `SELECT current_status FROM shipments WHERE tracking_number = 'BD-987654321';`.
  - Current status remains **`IN_TRANSIT`**! It did **not** regress to `PICKED_UP`!
  - In `shipment_tracking_events`, the audit record is preserved with `processing_result = 'OUT_OF_ORDER_RECORDED'`.

---

### Minute 5:30 – 6:30: Demo 5 – Quarantine Buffer & Batch Reconciliation
- **Action in Postman**: Select:  
  **`POST Unknown Shipment Scan (Quarantine Buffer)`**
- **What to Explain**:  
  *"A driver scans tracking number `DELH-99887766` which has not yet been registered in our WMS. Instead of dropping the scan or crashing, we quarantine it."*
- **Click**: **Send**
- **Judge Observation**: Returns `QUARANTINED_PENDING_REGISTRATION`, `isPendingUnknown: true`.
- **Action in MySQL Workbench**: Show record in `pending_tracking_events`.
- **Action in Postman**: Select:  
  **`POST Reconcile Quarantined Events Batch`**
- **Click**: **Send**
- **Judge Observation**: Returns `reconciledCount: 1`, `status: "RECONCILIATION_COMPLETED"`. The scan has been automatically moved from quarantine to the active tracking history!

---

### Minute 6:30 – 7:30: Demo 6 – Explainable Delay Risk Engine
- **Action in Postman**: Select:  
  **`GET Explainable Risk Assessment (Delayed SLA)`**
- **Endpoint**: `GET {{baseUrl}}/shipments/BD-123456789/risk`
- **What to Explain**:  
  *"Our risk engine dynamically calculates whether a parcel is on schedule or breaching customer promises. For shipment `BD-123456789`, the promised delivery time was yesterday, but the parcel is still in transit."*
- **Click**: **Send**
- **Judge Observation**:  
  - Returns `riskLevel: "DELAYED"`.
  - Returns human-readable explanation: `"Promised delivery deadline has passed. Current shipment status is IN_TRANSIT."`
  - Returns exact risk factors array: `["Promised SLA: 2026-10-10 12:00:00", "Current time exceeds deadline"]`.

---

### Minute 7:30 – 8:30: Demo 7 – Operational Telemetry & Automated Test Proof
- **Action in Postman**: Select:  
  **`GET Carrier Pulse Metrics & Telemetry`**
- **Click**: **Send**
- **Judge Observation**: Returns real-time aggregated metrics across BlueDart and Delhivery (total scans, processed count, duplicates suppressed, out-of-order count, and active shipments).
- **Action in Anypoint Studio**: Show the **MUnit view** with **9/9 green tests passing**.
- **Closing Statement**:  
  *"In conclusion, the Shipment Signal Control Tower delivers end-to-end multi-carrier normalization, zero message loss via the Transactional Outbox, complete idempotency, forward-only state integrity, and proactive SLA breach visibility. Thank you, and we welcome your questions!"*
