# 19 – Structured Logging, Observability & Carrier Pulse Telemetry

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Logging Framework**: Apache Log4j2 (Asynchronous Disruptor-based Logging)  
**Configuration File**: `src/main/resources/log4j2.xml`  

---

## 1. Structured Logging Strategy & Correlation Context

In high-volume integration architectures, debugging requests across asynchronous boundaries requires strict contextual tracing.

Every inbound transaction in the **Shipment Signal Control Tower** is tagged with an immutable **Distributed Correlation ID**:
1. Extracted from header `X-Correlation-ID` if supplied by the caller.
2. If absent, synthesized dynamically using DataWeave `uuid()`.
3. Propagated through every downstream flow, logger, database query, outbox record, and HTTP response header.

```text
[HTTP Ingress] POST /api/v1/webhooks/carriers/DELHIVERY | CorrelationId: REAL-MAIL-TEST-003
  ├── [Security] Authenticated webhook for carrier: DELHIVERY
  ├── [Normalizer] Delhivery normalized to Canonical Status: OUT_FOR_DELIVERY | EventKey: DELHIVERY-DELH-11223344-OFD-20261012160500
  ├── [State Progression] Valid forward progression: PICKED_UP (20) -> OUT_FOR_DELIVERY (40)
  ├── [Notification Queue] Enqueueing email alert for Tracking: DELH-11223344 | Milestone: OUT_FOR_DELIVERY
  └── [Async Consumer] [Live Email Dispatch SUCCESS] Sent milestone email to sridharthadicharla@gmail.com
```

---

## 2. Standardized Log Level Usage

| Log Level | Purpose & Example Message | Code Location |
|---|---|---|
| **INFO** | Transaction lifecycle milestones.<br>`[HTTP Ingress] POST /api/v1/webhooks/carriers/BLUEDART | CorrelationId: c85d8984...` | Ingress flows, state progression, outbox publishing. |
| **WARN** | Recoverable operational anomalies.<br>`[Out-of-Order] Stale/Older event received for Shipment SHP-1001. Preserving in history without regressing current status: DELIVERED` | Anti-regression engine, idempotency detection, quarantine events. |
| **DEBUG** | Detailed diagnostic data.<br>`[Security] Authenticated webhook for carrier: BLUEDART` | Security subflows, raw DataWeave payload evaluation. |
| **ERROR** | Unhandled exceptions and system failures.<br>`[Error Handler] Database connection refused during master update.` | `globalError_Handler` in `error-handling.xml`. |

---

## 3. Data Protection: What Is Never Logged

To comply with enterprise security and data privacy standards (GDPR, PCI-DSS):
1. **Carrier Authentication Tokens**: In `subflow-validate-carrier-auth`, the application logs whether the token was `'NONE'` or `'INVALID'`. The **actual raw secret is NEVER logged**.
2. **Database Passwords**: Connection string passwords are injected via properties and stripped from logs.
3. **Customer Personal Data**: Raw recipient email addresses are masked or logged only at trace levels.

---

## 4. Operational Telemetry & Monitoring Endpoints

### 4.1 Health Check API (`GET /api/v1/health`)
Probes the health of underlying subsystems and returns JSON:
```json
{
  "status": "UP",
  "service": "Shipment Signal Control Tower API",
  "version": "1.0.0",
  "environment": "dev",
  "database": "CONNECTED",
  "queue": "CONNECTED",
  "timestamp": "2026-10-13T12:00:00Z"
}
```

### 4.2 Carrier Pulse Telemetry (`GET /api/v1/carriers/pulse`)
Executes real-time SQL aggregation across `shipments`, `shipment_tracking_events`, and `pending_tracking_events` to report partner performance:
```json
[
  {
    "carrier": "BLUEDART",
    "totalEventsReceived": 142,
    "successfullyProcessed": 130,
    "duplicateEvents": 8,
    "outOfOrderEvents": 4,
    "unknownStatusEvents": 0,
    "pendingUnknownShipments": 0,
    "activeShipmentCount": 24,
    "healthStatus": "HEALTHY"
  },
  {
    "carrier": "DELHIVERY",
    "totalEventsReceived": 98,
    "successfullyProcessed": 85,
    "duplicateEvents": 5,
    "outOfOrderEvents": 6,
    "unknownStatusEvents": 0,
    "pendingUnknownShipments": 2,
    "activeShipmentCount": 18,
    "healthStatus": "HEALTHY"
  }
]
```

---

## 5. How to Inspect Logs During Evaluation

### In Anypoint Studio (Local Demo):
1. View the **Console** tab at the bottom of Anypoint Studio.
2. Click the **Clear Console** button before sending a Postman request.
3. Send the request in Postman.
4. Watch the structured log stream display the exact ingress, normalization, database commit, and queue dispatch sequence in real time.

### In CloudHub (Production):
1. Open **Anypoint Platform -> Runtime Manager**.
2. Click on application `shipment-tracking-control-tower`.
3. In the left navigation, click **Logs**.
4. Use the search bar to filter by correlation ID:
   `priority:INFO "DEMO-HAPPY-PATH-101"`
