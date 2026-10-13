# Shipment Signal Control Tower – Real-Time Multi-Carrier Tracking

**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  
**Technology Stack**: MuleSoft Mule 4 (Runtime 4.12.1 / 4.4.x), RAML 1.0, APIKit Router, DataWeave 2.0, MySQL 8.0, Anypoint VM Connector / Anypoint MQ, MUnit 3.3.0  

---

## 1. Executive Summary

In enterprise logistics networks, shippers integrate with diverse third-party logistics (3PL) carriers such as **BlueDart Express** and **Delhivery Logistics**. Each carrier provides independent webhook schemas, asynchronous push formats, out-of-order scan delivery, and differing status code naming conventions.

The **Shipment Signal Control Tower** provides an event-driven integration layer that:
1. Ingests carrier webhook push events securely via token authentication (`POST /webhooks/carriers/{carrierCode}`).
2. Normalizes diverse carrier payloads into a unified **Canonical Lifecycle Event Model**.
3. Enforces **strict idempotency** to prevent duplicate scan processing.
4. Preserves **forward-only shipment status progression** (protecting master state against out-of-order or stale scans).
5. Quarantines scans for unmanifested tracking numbers into a **quarantine buffer** with auto-reconciliation.
6. Computes an **Explainable Delay Risk Score** comparing carrier ETAs against customer promised SLAs (`ON_TRACK`, `AT_RISK`, `DELAYED`, `CRITICAL`).
7. Filters customer-facing milestones and guarantees zero message loss using a **Transactional Notification Outbox** and persistent asynchronous message queue.

---

## 2. Implemented Endpoints

| HTTP Method | Resource Path | Description | Authentication |
|---|---|---|---|
| `POST` | `/api/v1/webhooks/carriers/{carrierCode}` | Primary multi-carrier webhook ingestion | `X-Carrier-Token` |
| `POST` | `/api/v1/webhooks/bluedart` | Direct BlueDart webhook route | `X-Carrier-Token` |
| `POST` | `/api/v1/webhooks/delhivery` | Direct Delhivery webhook route | `X-Carrier-Token` |
| `POST` | `/api/v1/shipments` | Register / seed shipment master record | Public / Internal |
| `GET` | `/api/v1/shipments/{trackingNumber}` | Retrieve current shipment state & SLA status | Public |
| `GET` | `/api/v1/shipments/{trackingNumber}/history` | Chronological event audit trail | Public |
| `GET` | `/api/v1/shipments/{trackingNumber}/risk` | Explainable risk assessment & SLA breach analysis | Public |
| `GET` | `/api/v1/health` | Operational health check (Database & Queue connectivity) | Public |
| `GET` | `/api/v1/carriers/pulse` | Aggregated carrier telemetry & anomaly metrics | Operator |
| `POST` | `/api/v1/events/replay` | Operator replay of quarantined pending events | Operator |
| `POST` | `/api/v1/events/reconcile` | Batch reconciliation of pending events | Operator |

---

## 3. Database Schema (MySQL 8.0)

The application connects to MySQL database `shipment_control_tower` with 5 relational tables:
- `shipments`: Master tracking state and current SLA risk.
- `shipment_tracking_events`: Immutable audit trail with unique idempotency key.
- `pending_tracking_events`: Quarantine buffer for scans arriving before shipment registration.
- `notification_outbox`: Transactional outbox guaranteeing milestone delivery.
- `integration_alerts`: Operational telemetry recording exceptions and SLA breaches.

---

## 4. Quick Start Commands

```bash
# 1. Initialize MySQL Database & Sample Data
mysql -u root -p < database/schema.sql
mysql -u root -p < database/sample-data.sql

# 2. Compile Application via Maven
mvn compile -DskipTests

# 3. Import and Run in Anypoint Studio
# Right-click project -> Run As -> Mule Application
```
