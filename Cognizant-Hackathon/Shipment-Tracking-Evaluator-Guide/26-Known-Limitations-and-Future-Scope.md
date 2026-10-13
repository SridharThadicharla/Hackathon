# 26 – Known Limitations, Gaps & Production Roadmap

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0)  

---

## 1. Complete Transparency: Current Limitations & Gaps

To demonstrate architectural maturity during technical evaluation, a candidate must openly articulate what the current implementation does **not** do:

| Architectural Component | Current Prototype Reality | Production Enterprise Requirement | Current Status |
|---|---|---|---|
| **Carrier Security** | Shared secret comparison (`X-Carrier-Token` header). | Cryptographic HMAC-SHA256 signature verification with timestamp replay protection. | **IMPLEMENTED AND VERIFIED** (Token Auth) |
| **API Management** | Edge routing handled directly in Mule code via APIKit. | Automated policy governance via Anypoint API Manager (Rate Limiting, IP Whitelist). | **IMPLEMENTED — NOT VERIFIED** (Autodiscovery staged) |
| **Messaging Infrastructure** | Intra-JVM persistent VM queue (`mule-vm-connector`). | Distributed multi-AZ cloud broker (Anypoint MQ or Apache Kafka). | **IMPLEMENTED AND VERIFIED** (Local VM) |
| **Deployment Model** | Logical 3-layer architecture in a single Mule application. | Three physically decoupled CloudHub microservices (`eapi`, `papi`, `sapi`). | **IMPLEMENTED AND VERIFIED** (Logical Layers) |
| **Outbox Channels** | Live SMTP email functional; SMS/WhatsApp listed in data model. | Live integration with commercial SMS/WhatsApp gateway (Twilio, Gupshup). | **PARTIALLY IMPLEMENTED** |
| **Database Scalability** | Single local MySQL 8.0 instance. | Multi-AZ Amazon Aurora MySQL cluster with read replicas. | **IMPLEMENTED AND VERIFIED** (Local MySQL) |
| **Lifecycle Linearity** | Integer status rank comparison (`10` to `50`). | Dynamic Directed Acyclic Graph (DAG) state machine for multi-hop re-attempts. | **IMPLEMENTED AND VERIFIED** (Rank Machine) |

---

## 2. Detailed Technical Explanations of Current Gaps

### 1. Single Application vs. Physical Microservices
- **Reality**: Experience, Process, and System layers are packaged inside `shipment-tracking-control-tower.jar`.
- **Why It Exists**: Avoided the cost, multi-worker licensing, and network hop latency of three separate CloudHub applications during prototype development.
- **Production Path**: The code is already cleanly organized into separate files (`webhook-api.xml`, `shipment-processing.xml`, `database-operations.xml`). In under two hours, each file can be placed into a standalone Maven project with its own RAML interface.

### 2. Local VM Queues vs. Anypoint MQ
- **Reality**: The asynchronous milestone queue runs inside the JVM using local disk persistence.
- **Limitation**: If the application scales to 2 or 4 CloudHub workers, VM queues on Worker 1 cannot be read by Worker 2.
- **Production Path**: Replace `mule-vm-connector` with `anypoint-mq-connector:3.x`. The outbox table schema and milestone filter logic remain 100% identical.

### 3. Shared Token vs. HMAC Signatures
- **Reality**: Couriers authenticate by passing an API secret in the header.
- **Limitation**: While secure over TLS, it does not prove that the JSON payload body was not tampered with in transit.
- **Production Path**: Add a DataWeave HMAC validator in `subflow-validate-carrier-auth` to verify `X-Hub-Signature: sha256=<hash>`.

---

## 3. Production Hardening Roadmap (Sprint Plan)

```mermaid
gantt
    title Production Hardening Roadmap
    dateFormat  YYYY-MM-DD
    section Sprint 1: Security & Cloud
    Anypoint MQ Migration          :done, s1, 2026-11-01, 7d
    HMAC-SHA256 Webhook Verification:active, s2, after s1, 5d
    API Manager Auto-Discovery     :s3, after s2, 4d
    section Sprint 2: Multi-Channel & Scale
    Twilio Live SMS / WhatsApp     :s4, 2026-11-17, 7d
    Aurora MySQL Multi-AZ Peering   :s5, after s4, 5d
    Grafana / Datadog Log Forwarding:s6, after s5, 4d
```

### Sprint 1: Enterprise Security & Cloud Messaging
1. **Transition VM Queues to Anypoint MQ**: Provision standard FIFO queues in Anypoint Platform MQ for zero-loss multi-worker clustering.
2. **Implement HMAC Cryptographic Verification**: Use `dw::Crypto::HMACBinary` to validate message integrity against courier public keys.
3. **Bind API Auto-Discovery**: Apply rate-limiting policies (1,000 req/min per courier) in API Manager.

### Sprint 2: Multi-Channel Messaging & Database Clustering
1. **Twilio REST Connector**: In `flow-consume-milestone-notification`, add a parallel branch to transmit SMS and WhatsApp messages alongside HTML emails.
2. **AWS Aurora MySQL Deployment**: Provision multi-AZ database clustering with read replicas for real-time tracking queries.
3. **Observability Pipeline**: Stream Log4j2 logs into Datadog or Splunk for enterprise logistics dashboards.
