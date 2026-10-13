w4e3ar4rswc xq              qa     aq v# 01 – Project Overview: Real-Time Multi-Carrier Shipment Tracking

**Project**: Shipment Signal Control Tower  
**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  

---

## 1. Business Problem & Industry Context

Modern e-commerce enterprises, third-party logistics (3PL) providers, and supply chain operators depend on multiple regional and national couriers to fulfill consumer and B2B orders. In the Indian logistics ecosystem, carriers like **BlueDart Express** (aviation / express network) and **Delhivery Logistics** (surface / ground freight) power a significant share of parcel movements.

However, integrating multi-carrier tracking feeds presents 5 major technical and operational challenges:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       CHALLENGES IN MULTI-CARRIER LOGISTICS                     │
├────────────────────────┬────────────────────────────────────────────────────────┤
│ 1. Heterogeneous       │ BlueDart sends JSON with 'awb_no', 'status_code' (UD,  │
│    Data Formats        │ PU, IT), and ISO+offset timestamps; Delhivery sends    │
│                        │ 'waybill', nested 'Status', 'Scans' array, and space-  │
│                        │ separated timestamps ('2026-10-10 11:45:00').          │
├────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Webhook Duplication │ Cellular drops and carrier retry policies frequently   │
│                        │ result in identical scans being sent 3 to 5 times,     │
│                        │ risking customer notification spam and race conditions.│
├────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. Out-of-Order Scans  │ Delivery vans operating in low-connectivity areas may  │
│                        │ upload earlier hub scans AFTER a delivery agent has    │
│                        │ already marked a parcel OUT_FOR_DELIVERY. Naive        │
│                        │ systems accidentally overwrite master states backwards!│
├────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. Unmanifested Scans  │ Courier drivers scan packages at origin before the WMS │
│    (Ghost Shipments)   │ order batch has finished publishing to tracking tables.│
│                        │ Dropping these scans causes complete visibility loss.  │
├────────────────────────┼────────────────────────────────────────────────────────┤
│ 5. Blind SLA Breaches  │ Shippers only discover delays when an angry customer   │
│                        │ calls support, because carriers report revised ETAs    │
│                        │ without proactively flagging SLA breaches.             │
└────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 2. The Solution: Shipment Signal Control Tower

The **Shipment Signal Control Tower** is an enterprise-grade integration system built natively on MuleSoft Mule 4. It acts as an authoritative, real-time control layer between disparate logistics carriers and customer-facing touchpoints (WMS, ERP, customer mobile app, customer support portal).

```
[BlueDart Webhook] ───┐
                      ├──► [Ingress Router: /webhooks/carriers/{carrierCode}]
[Delhivery Webhook] ──┘                 │
                                        ▼
                        [Carrier Auth Validation: Token Check]
                                        │
                                        ▼
                        [DataWeave Normalizer to Canonical Event]
                                        │
                       ┌────────────────┴────────────────┐
                       ▼                                 ▼
             [Idempotency Filter]              [Master Shipment Lookup]
             (Check event_key)                 (Lookup tracking_number)
                       │                                 │
           ┌───────────┴──────────┐            ┌─────────┴─────────┐
           ▼                      ▼            ▼                   ▼
    [Duplicate Found]     [Fresh Event]   [Found in DB]     [Unknown / Not Found]
    (Return ACK 200)              │            │                   │
    (Suppress Outbox)             └─────┬──────┘                   ▼
                                        ▼                 [Quarantine Buffer]
                            [Status Progression Rules]   (pending_tracking_events)
                            (Prevent Rank Regression)              │
                                        │                          ▼
                                        ▼                 [Auto-Reconciliation]
                            [Risk Engine: SLA vs ETA]
                            (ON_TRACK, AT_RISK, DELAYED)
                                        │
                                        ▼
                            [MySQL Transactional DB]
                            (shipments & audit events)
                                        │
                                        ▼
                       ┌────────────────┴────────────────┐
                       ▼                                 ▼
            [Transactional Outbox]             [Asynchronous VM Queue]
           (notification_outbox)             (shipment-milestone-queue)
                       │                                 │
                       └────────────────┬────────────────┘
                                        ▼
                             [Notification Consumer]
                             (Multi-Channel Dispatch)
```

---

## 3. Core Functional Capabilities

### 3.1 Unified Canonical Event Model
Standardizes every carrier event into an immutable canonical contract with the 9 official Use Case 08 lifecycle milestones:
- `LABEL_CREATED`: Package manifested and electronic shipping label created.
- `PICKED_UP`: Physical custody transferred to carrier agent.
- `IN_TRANSIT`: Linehaul movement between freight centers.
- `ARRIVED_AT_HUB`: Package scanned at a regional sorting facility.
- `OUT_FOR_DELIVERY`: Package assigned to courier for last-mile delivery.
- `DELIVERY_ATTEMPTED`: Delivery attempted but customer unavailable.
- `DELIVERED`: Physical handover confirmed with consignee signature/OTP.
- `RETURNED`: Undeliverable shipment returned to origin warehouse.
- `EXCEPTION`: Operational incident (weather delay, damaged goods, address issue).

### 3.2 Idempotent Deduplication Engine
Every event generates a deterministic composite key:
`event_key = CARRIER - TRACKING_NUMBER - STATUS_CODE - TIMESTAMP`  
If an incoming event key already exists in `shipment_tracking_events`, the pipeline immediately acknowledges receipt with `DUPLICATE_ACKNOWLEDGED`, suppressing duplicate DB writes and customer notification spam.

### 3.3 Forward-Only Status Progression (No State Downgrades)
Each canonical status is assigned an integer `status_rank` (e.g. `LABEL_CREATED=10`, `PICKED_UP=20`, `IN_TRANSIT=30`, `ARRIVED_AT_HUB=35`, `OUT_FOR_DELIVERY=40`, `DELIVERED=50`). If an out-of-order scan arrives with an earlier timestamp or a lower status rank, the system preserves the scan in `shipment_tracking_events` for audit compliance, but **never regresses the current master shipment status**.

### 3.4 Quarantine Buffer & Auto-Reconciliation
When tracking events arrive for unmanifested tracking numbers, they are safely quarantined in `pending_tracking_events`. As soon as the WMS creates the shipment master record, the `/events/reconcile` batch pipeline automatically ingests and replays the quarantined scans.

### 3.5 Explainable Delay Risk Engine
Compares carrier revised ETAs and scan timestamps against the promised customer delivery SLA date:
- `ON_TRACK`: Progressing normally within delivery commitment.
- `AT_RISK`: Carrier ETA exceeds promised delivery deadline.
- `DELAYED`: Current timestamp has breached promised SLA commitment.
- `CRITICAL`: Delivery failure / exception occurred and SLA breached.
- `UNKNOWN`: Insufficient SLA benchmark data.

### 3.6 Transactional Notification Outbox Pattern
Customer notifications for critical milestones (`PICKED_UP`, `OUT_FOR_DELIVERY`, `DELIVERY_ATTEMPTED`, `DELIVERED`, `EXCEPTION`) are persisted directly into `notification_outbox` before dispatching to persistent VM queues, guaranteeing at-least-once delivery with zero message loss.
