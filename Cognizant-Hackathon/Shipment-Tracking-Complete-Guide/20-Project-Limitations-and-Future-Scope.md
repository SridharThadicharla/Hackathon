# 20 – Project Limitations & Future Scope Architectural Roadmap

**Project**: Shipment Signal Control Tower  
**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  

---

## 1. Current Project Scope & Intentional Design Trade-offs

In line with enterprise architecture standards and hackathon requirements, the current implementation prioritizes rock-solid reliability, zero message loss, forward-only state integrity, and explainable SLA breach visibility.

To ensure transparency before judges, the following boundaries and intentional design choices are noted:

```text
┌─────────────────────────────────┬─────────────────────────────────┐
│     CURRENT IMPLEMENTATION      │    ENTERPRISE BOUNDARY / REASON │
├─────────────────────────────────┼─────────────────────────────────┤
│ 1. Pre-Shared Secret Tokens     │ Standard for 3PL webhook pushes;│
│    (X-Carrier-Token)            │ avoids complex OAuth handshake  │
│                                 │ on asynchronous fire-and-forget.│
├─────────────────────────────────┼─────────────────────────────────┤
│ 2. Local Persistent VM Queues   │ Zero external cloud broker      │
│    (VM Connector)               │ dependency; runnable offline on │
│                                 │ any developer machine.          │
├─────────────────────────────────┼─────────────────────────────────┤
│ 3. Rule-Based Explainable Risk  │ Deterministic SLA compliance;   │
│    Engine                       │ 100% explainable to judges and  │
│                                 │ audit teams without black-box ML│
├─────────────────────────────────┼─────────────────────────────────┤
│ 4. Single-Region MySQL 8.0      │ High performance ACID relational│
│                                 │ database for local validation.  │
└─────────────────────────────────┴─────────────────────────────────┘
```

---

## 2. Five-Phase Enterprise Evolution Roadmap

### Phase 1: Advanced Security & HMAC Verification
- **Cryptographic Signatures**: Implement HMAC-SHA256 request signing using carrier-specific secret keys (`X-Hub-Signature-256`), eliminating replay attacks.
- **Mutual TLS (mTLS)**: Enforce bidirectional certificate-based authentication on the CloudHub Dedicated Load Balancer (DLB).
- **MuleSoft Anypoint Flex Gateway**: Deploy ultra-low latency Envoy-based Flex Gateways at the edge for sub-millisecond policy enforcement.

### Phase 2: Apache Kafka / Anypoint MQ Streaming at Scale
- **Event Streaming Backbone**: Transition from local VM queues to Apache Kafka or Anypoint MQ for high-throughput partitioning.
- **Partitioning by Carrier / Pin Code**: Partition tracking streams by geographic destination pin code to guarantee strict per-package FIFO ordering even under massive concurrency (50,000+ events/sec).
- **Change Data Capture (CDC)**: Implement Debezium / Kafka Connect for automated streaming of WMS manifest events directly into the control tower.

### Phase 3: AI-Powered Predictive Delay & ETA Engine
- **MuleSoft AI Chain & Einstein Integration**: Complement the current rule-based SLA engine with machine learning models trained on historical transit times.
- **Dynamic Weather & Traffic Factors**: Integrate live meteorological feeds and national highway congestion APIs to predict delays 12 to 24 hours *before* the carrier reports an updated ETA.

### Phase 4: Full Reverse Logistics & Autonomous Exceptions
- **Autonomous RTO Handling**: Automatically issue reverse return pickup requests when a parcel transitions into `RETURNED` or fails 3 consecutive delivery attempts.
- **Customer Self-Service Rescheduling**: Send interactive WhatsApp / SMS links allowing customers to reschedule delivery windows dynamically upon receiving an `EXCEPTION` notification.

### Phase 5: Multi-Cloud Active-Active Resilience
- **Multi-Region CloudHub 2.0**: Deploy twin replicas across AWS `us-east-1` and `ap-south-1` (Mumbai) with Amazon Route 53 latency-based routing.
- **Distributed Database Clustering**: Deploy AWS Aurora MySQL Global Database with multi-master write replication across availability zones.
