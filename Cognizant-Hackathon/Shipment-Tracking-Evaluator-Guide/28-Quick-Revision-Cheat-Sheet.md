# 28 – Pre-Interview Quick Revision Cheat Sheet (10-Minute Read)

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0 EE / MySQL 8.0)  

---

## 1. Project at a Glance

- **Use Case**: 08 (Logistics — Multi-Carrier Tracking for BlueDart Express & Delhivery Logistics).
- **Core Problem**: Incompatible carrier JSON schemas, network duplicates, out-of-order scans regressing state, unmanifested scans dropped, and notification spam.
- **Solution**: Contract-first Mule 4 application with DataWeave normalizers, dual-layer deduplication, anti-regression status ranking, unmanifested quarantine buffer, explainable SLA risk scoring, and asynchronous transactional outbox messaging.

---

## 2. Architecture & File Reference

```text
Experience Layer: webhook-api.xml (HTTP :8081 /api/v1/*, Token Auth, APIKit Router, Console :8081/console/)
Process Layer:    carrier-normalization.xml (DWL), shipment-processing.xml (Core), risk-assessment.xml (SLA)
System Layer:     database-operations.xml (MySQL), notification-queue.xml (VM Queue & SMTP Email)
```

- **5 Database Tables**:
  1. `shipments`: Master state, latest forward status, status rank, promised SLA, risk level.
  2. `shipment_tracking_events`: Immutable audit trail with `UNIQUE KEY (event_key)`.
  3. `pending_tracking_events`: Quarantine buffer holding unmanifested parcel scans.
  4. `notification_outbox`: Transactional outbox holding customer alerts (`QUEUED` $\rightarrow$ `SENT`).
  5. `integration_alerts`: Operational anomaly and exception log.
- **5 Connectors**:
  - `HTTP` (`HTTP_Listener_config` on `0.0.0.0:8081`).
  - `APIKit` (`shipment-tracking-config` bound to `api/shipment-tracking.raml`).
  - `Database` (`Database_Config` - MySQL 8.0 with `serverTimezone=UTC`).
  - `VM` (`VM_Config` - persistent FIFO queue `shipment-milestone-queue`).
  - `Email` (`Email_SMTP` - STARTTLS port 587).

---

## 3. Core Business Logic Rules

1. **Deterministic Idempotency**:
   - `eventKey = <CARRIER>-<TRACKING>-<STATUS>-<TIMESTAMP>`.
   - Verified via `subflow-check-duplicate-event` and MySQL unique constraint.
   - If duplicate $\rightarrow$ returns HTTP 200 `DUPLICATE_ACKNOWLEDGED`, zero database mutation.
2. **Numeric Status Ranking & Anti-Regression**:
   - `LABEL_CREATED (10)` $\rightarrow$ `PICKED_UP (20)` $\rightarrow$ `IN_TRANSIT (30)` $\rightarrow$ `ARRIVED_AT_HUB (35)` $\rightarrow$ `OUT_FOR_DELIVERY (40)` $\rightarrow$ `DELIVERED (50)` $\rightarrow$ `RETURNED (60)`.
   - If `newRank < currentRank` or scan is older $\rightarrow$ flagged as `isOutOfOrder`.
   - Scan appended to audit ledger, **master state is NOT regressed**, returns HTTP 200 `OUT_OF_ORDER_RECORDED`.
3. **Quarantine Buffer & Batch Reconcile**:
   - Unregistered tracking numbers buffered into `pending_tracking_events` with status `PENDING`.
   - Returns HTTP 200 `QUARANTINED_PENDING_REGISTRATION`.
   - Reconciled via `POST /events/reconcile` once WMS manifests order.
4. **Explainable SLA Risk Engine**:
   - `eventTimestamp > promisedDeliveryTime` $\rightarrow$ `DELAYED` (`PROMISED_SLA_BREACHED`).
   - In-transit without update for >48h $\rightarrow$ `AT_RISK` (`STALE_TRANSIT`).
   - ETA > promised SLA by >24h $\rightarrow$ `DELAYED` (`CRITICAL_DELAY`).
   - ETA > promised SLA by >6h $\rightarrow$ `AT_RISK` (`SLA_BREACH_WARNING`).
5. **Milestone Filter & Transactional Outbox**:
   - Customer alerts triggered **only** for: `PICKED_UP`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`, `DELIVERY_ATTEMPTED`.
   - Routine transit scans (`IN_TRANSIT`, `ARRIVED_AT_HUB`) **suppress alerts by design**.
   - Alert inserted into `notification_outbox` (`QUEUED`), published to VM queue, webhooks return in `<50ms`.
   - Background VM consumer renders HTML email, transmits via SMTP, updates outbox to `SENT`.

---

## 4. Top 10 Rapid-Fire Answers for the Interview Panel

1. **Why MuleSoft?** Automated RAML validation via APIKit, high-performance DataWeave transformation, asynchronous VM queues, and declarative error routing.
2. **How do you handle duplicates?** Deterministic composite `eventKey` construction paired with a MySQL `UNIQUE KEY` constraint. Returns `DUPLICATE_ACKNOWLEDGED`.
3. **How do you prevent state regression?** Integer status ranks (`10` to `50`). A scan with rank 20 cannot overwrite rank 50 (`DELIVERED`).
4. **What happens if a parcel isn't in the database?** Quarantined into `pending_tracking_events` (`200 OK`). Auto-reconciled later via `POST /events/reconcile`.
5. **How are customer alerts decoupled?** Transactional Outbox Pattern: Alert saved to database, published to persistent VM queue; webhook acknowledges in `<50ms`; VM consumer sends email.
6. **Why don't customers get spammed?** Milestone filter allows only 5 major lifecycle events; routine transit hops (`IN_TRANSIT`) are suppressed by design.
7. **Is it deployed as three separate APIs?** Implemented as logical Experience, Process, and System tiers in a single deployable Mule application for performance and hackathon evaluation; can be split into three CloudHub APIs without refactoring business logic.
8. **What tests exist?** 9 automated MUnit test suites covering DataWeave mappings, token security, duplicate suppression, quarantine, SLA risk, and milestone filtering.
9. **How do you handle timezones?** Carrier localized IST timestamps (`+05:30`) are converted to UTC ISO-8601 strings (`yyyy-MM-dd'T'HH:mm:ss'Z'`) in DataWeave.
10. **What would you improve for production?** Replace local VM queues with Anypoint MQ, implement HMAC-SHA256 webhook signatures, and add Twilio live SMS dispatch.
