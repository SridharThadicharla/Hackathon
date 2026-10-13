# 04 – Architecture & API-Led Connectivity Guide

**Project**: Shipment Signal Control Tower  
**Architecture Methodology**: MuleSoft API-Led Connectivity & Event-Driven Architecture (EDA)  

---

## 1. MuleSoft API-Led Connectivity in Logistics

MuleSoft's **API-Led Connectivity** is an architectural framework that structures integration assets into three discrete, reusable tiers: **Experience APIs**, **Process APIs**, and **System APIs**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        EXPERIENCE LAYER (X-APIs)                       │
│  - Carrier Webhook Ingress API (/webhooks/carriers/{carrierCode})      │
│  - Customer Tracking Portal Experience API (/shipments/{awb})          │
│  - Tower Operations Telemetry API (/carriers/pulse)                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         PROCESS LAYER (P-APIs)                         │
│  - Canonical Normalization Engine (DataWeave 2.0 CDM)                  │
│  - Idempotency & Deduplication Service (event_key hashing)             │
│  - State Machine & Forward-Only Progression Enforcer                   │
│  - Explainable Delay Risk Engine (SLA Breach Evaluator)                │
│  - Customer Milestone Notification Outbox Dispatcher                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM LAYER (S-APIs)                          │
│  - MySQL 8.0 Relational Persistence Layer (shipments, audit events)    │
│  - Asynchronous Message Broker (Anypoint VM / Anypoint MQ)             │
│  - Downstream SMS / Email / Webhook Gateway Adapters                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Why 3-Tier Layering Solves Logistics Chaos
In traditional point-to-point architectures, every carrier integration is tightly coupled directly to internal databases and notification services. Integrating $N$ carriers with $M$ internal systems requires $N \times M$ fragile custom interfaces.

By introducing the **Canonical Event Model** in the Process Layer, integrating a new carrier (e.g. FedEx, DTDC, Shadowfax) only requires adding a single DataWeave normalizer mapping to the canonical contract. The rest of the pipeline—deduplication, master state updates, SLA calculations, and notification dispatch—is reused without modifying a single line of backend logic ($N + M$ scaling).

---

## 2. Event-Driven Architecture (EDA) & Decoupling

Carrier webhooks are bursty by nature. During peak festival seasons (e.g. Diwali sales), thousands of parcel scans flood the ingress endpoint simultaneously.

To ensure high throughput and zero message loss:
1. **Synchronous Fast-Path (HTTP Ingress)**:
   - Validates authentication token in `< 5ms`.
   - Normalizes payload to canonical event model.
   - Enforces database idempotency check.
   - Updates shipment master state.
   - Persists milestone alert in `notification_outbox`.
   - Publishes milestone event to an asynchronous persistent queue.
   - Immediately returns HTTP `200 OK` acknowledgment to the courier webhook.
2. **Asynchronous Slow-Path (Message Consumer)**:
   - Consumes messages from persistent VM queue `shipment-milestone-queue`.
   - Dispatches multi-channel customer alerts (SMS, Email, Push).
   - Marks the outbox record as `SENT`.

```text
Carrier Push ──► HTTP Listener ──► Normalize & Deduplicate ──► DB Transaction
                                                                     │
                                     HTTP 200 ACK ◄──────────────────┤
                                                                     ▼
                                                          Persist Outbox (DB)
                                                                     │
                                                                     ▼
                                                          Publish to VM Queue
                                                                     │
                                                                     ▼
                                                      [Asynchronous Consumer]
                                                                     │
                                                                     ▼
                                                          External Alert (SMS)
```

---

## 3. Resilience Design Patterns

### 3.1 Idempotency Key Pattern
Network timeouts between carrier webhook engines and the control tower often cause carriers to retry identical POST requests. The Control Tower derives a deterministic idempotency key for every payload:
```text
event_key = CarrierPrefix + TrackingNumber + StatusCode + TimestampCompact
Example: BLUEDART-BD-987654321-IT-20261011103000
```
This key is indexed with a `UNIQUE` constraint in MySQL table `shipment_tracking_events`. If a duplicate is received, the flow catches it, logs a warning, and returns HTTP 200 with `DUPLICATE_ACKNOWLEDGED`, preventing duplicate DB inserts or redundant customer alerts.

### 3.2 State Machine Protection (Forward-Only Progression)
In real-world logistics, linehaul drivers in rural areas often sync earlier terminal scans after a parcel is already marked `DELIVERED`. The Control Tower uses status ranks:
- `LABEL_CREATED` (10)
- `PICKED_UP` (20)
- `IN_TRANSIT` (30)
- `ARRIVED_AT_HUB` (35)
- `OUT_FOR_DELIVERY` (40)
- `DELIVERY_ATTEMPTED` (45)
- `DELIVERED` (50)
- `RETURNED` (60)

If incoming scan rank is less than current rank or the event timestamp is older than `last_event_timestamp`, it is classified as `OUT_OF_ORDER_RECORDED`. It is preserved in the audit table for tracking transparency, but **does not overwrite the master shipment status**.

### 3.3 Transactional Outbox Pattern
Directly publishing to external SMS/email APIs inside the HTTP webhook flow introduces failure points if the external API is unreachable. By persisting alerts in the `notification_outbox` table first, the system guarantees that even in complete network blackouts, notifications can be recovered and redelivered safely.
