# 18 – Six-Member Team Responsibilities & RACI Matrix

**Project**: Shipment Signal Control Tower  
**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  

---

## 1. Team Roles & Ownership Breakdown

To execute and defend an enterprise-grade project during a high-stakes hackathon, responsibilities are distributed among 6 specialized engineering roles:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   MULESOFT HACKATHON TEAM STRUCTURE                    │
├───────────────────────────────┬────────────────────────────────────────┤
│ Role 1: MuleSoft Lead         │ Architecture design, API-Led 3-tier    │
│         Architect             │ strategy, RAML 1.0 contract, review    │
├───────────────────────────────┼────────────────────────────────────────┤
│ Role 2: Mule 4 Backend        │ Ingress flows, APIKit routing, state   │
│         Developer             │ machine, quarantine & reconciliation   │
├───────────────────────────────┼────────────────────────────────────────┤
│ Role 3: DataWeave Specialist  │ Canonical Event model, DWL mappings for│
│                               │ BlueDart & Delhivery, risk rules engine│
├───────────────────────────────┼────────────────────────────────────────┤
│ Role 4: Database & SQL        │ MySQL 8.0 schema DDL, indexes, seed    │
│         Engineer              │ data, parameterized queries, pooling   │
├───────────────────────────────┼────────────────────────────────────────┤
│ Role 5: MUnit & QA Engineer   │ 9 MUnit automated test cases, mocks,   │
│                               │ 16-request Postman test collection     │
├───────────────────────────────┼────────────────────────────────────────┤
│ Role 6: DevOps & Deployment   │ CloudHub deployment, secure properties,│
│         Engineer              │ Log4j2, documentation & demo prep      │
└───────────────────────────────┴────────────────────────────────────────┘
```

---

## 2. Detailed Member Deliverables & Responsibilities

### Member 1: MuleSoft Lead Architect
- **Primary Deliverables**: `04-Architecture-and-API-Led-Connectivity.md`, `src/main/resources/api/shipment-tracking.raml`.
- **Core Tasks**:
  - Defined the 3-tier API-Led architecture separating Experience, Process, and System layers.
  - Authored the RAML 1.0 contract with data types, query traits, and RFC-7807 error responses.
  - Designed the idempotency hashing algorithm (`event_key`) and state progression rank hierarchy.
  - Leads the judge Q&A architectural defense.

### Member 2: Mule 4 Backend Developer
- **Primary Deliverables**: `src/main/mule/webhook-api.xml`, `src/main/mule/shipment-processing.xml`.
- **Core Tasks**:
  - Implemented the HTTP Ingress Listener and APIKit Router dispatchers.
  - Built the core event processing pipeline (`flow-process-canonical-event`).
  - Implemented the quarantine buffer logic and `/events/reconcile` batch auto-reconciliation.
  - Built operational endpoints (`/health`, `/carriers/pulse`, `/events/replay`).

### Member 3: DataWeave & Transformation Specialist
- **Primary Deliverables**: `src/main/resources/dw/bluedart-to-canonical.dwl`, `src/main/resources/dw/delhivery-to-canonical.dwl`, `src/main/mule/risk-assessment.xml`.
- **Core Tasks**:
  - Engineered the BlueDart and Delhivery DataWeave 2.0 transformations.
  - Built robust date/timestamp parsing handling IST offsets, UTC, and space-separated date strings.
  - Implemented the Explainable Delay Risk Engine calculating `ON_TRACK`, `AT_RISK`, `DELAYED`, and `CRITICAL`.

### Member 4: Database & SQL Engineer
- **Primary Deliverables**: `database/schema.sql`, `database/sample-data.sql`, `src/main/mule/database-operations.xml`.
- **Core Tasks**:
  - Designed all 5 MySQL 8.0 relational tables (`shipments`, `events`, `pending`, `outbox`, `alerts`).
  - Configured database indexes and unique constraints for rapid O(1) idempotency lookups.
  - Authored parameterized SQL statements in `database-operations.xml` to prevent SQL injection.
  - Configured MySQL connection pool settings, `serverTimezone=UTC`, and `autoReconnect=true`.

### Member 5: MUnit & QA Testing Specialist
- **Primary Deliverables**: `src/test/munit/shipment-tracking-test-suite.xml`, `postman/Shipment-Tracking.postman_collection.json`.
- **Core Tasks**:
  - Built 9 automated MUnit test scenarios covering positive, negative, and edge-case paths.
  - Configured test mocks (`munit-tools:mock-when`) for database queries and queue dispatches.
  - Authored the complete 16-request Postman test suite with environment variables.
  - Conducted load tests verifying deduplication and state machine protection.

### Member 6: DevOps, Security & Deployment Engineer
- **Primary Deliverables**: `pom.xml`, `mule-artifact.json`, `deployment/deployment-notes.md`, `src/main/resources/log4j2.xml`.
- **Core Tasks**:
  - Managed Maven build lifecycle, connector dependencies, and local JAR packaging.
  - Configured CloudHub 1.0 / 2.0 deployment descriptors and secure property masking.
  - Implemented Log4j2 pattern layouts and distributed correlation ID injection.
  - Coordinates the live 8-minute demonstration script and technical slides.

---

## 3. RACI Responsibility Assignment Matrix

| Workstream / Deliverable | Member 1 (Arch) | Member 2 (Backend) | Member 3 (DWL) | Member 4 (DB) | Member 5 (QA) | Member 6 (DevOps) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **RAML 1.0 Specification** | **A / R** | C | C | I | C | I |
| **Mule Ingress & Flows** | A | **R** | C | C | C | I |
| **DataWeave Mappings** | A | C | **R** | I | C | I |
| **MySQL 8.0 Database** | A | C | I | **R** | I | C |
| **Outbox & VM Queue** | A | **R** | I | C | I | C |
| **MUnit Test Suite** | A | C | C | I | **R** | I |
| **Postman Test Suite** | A | C | C | C | **R** | I |
| **CloudHub Deployment** | A | I | I | I | I | **R** |
| **Live Hackathon Demo** | **A** | R | R | R | R | **R** |

*(R = Responsible, A = Accountable, C = Consulted, I = Informed)*
