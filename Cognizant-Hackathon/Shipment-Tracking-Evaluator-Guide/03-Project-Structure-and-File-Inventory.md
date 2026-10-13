# 03 – Project Structure & Comprehensive File Inventory

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Root Path**: `Cognizant-Hackathon/Shipment-Signal-Control-Tower/`  
**Application Runtime**: Mule Runtime 4.4.0 (Enterprise Edition)  

---

## 1. Complete Physical Directory Tree

```text
Shipment-Signal-Control-Tower/
├── .project                                              # Eclipse/Anypoint Studio project metadata
├── .classpath                                            # Java & Mule classpath dependencies
├── mule-artifact.json                                    # Mule runtime descriptor & classloader configuration
├── pom.xml                                               # Maven Project Object Model (dependencies & plugins)
├── README.md                                             # High-level project documentation
├── database/
│   ├── schema.sql                                        # DDL: 5 MySQL tables, indexes, constraints
│   ├── sample-data.sql                                   # DML: Seed master shipments & outbox records
│   └── verification-queries.sql                          # SQL audit scripts for demo verification
├── deployment/
│   └── deployment-notes.md                               # CloudHub 1.0/2.0 deployment guide & runbook
├── postman/
│   ├── Shipment-Tracking.postman_collection.json         # 16 automated Postman request scenarios
│   └── local-environment.postman_environment.json       # Local runtime environment variables
└── src/
    ├── main/
    │   ├── mule/                                         # Mule 4 Flow Configuration XML Files
    │   │   ├── global-config.xml                         # Connectors, configurations, property source
    │   │   ├── webhook-api.xml                           # HTTP ingress, APIKit routing, APIKit console
    │   │   ├── carrier-normalization.xml                 # DataWeave router & normalization subflows
    │   │   ├── shipment-processing.xml                   # Idempotency, state machine, anti-regression
    │   │   ├── risk-assessment.xml                       # Explainable SLA risk engine
    │   │   ├── database-operations.xml                   # Low-level MySQL database CRUD subflows
    │   │   ├── notification-queue.xml                    # Milestone filter, VM publish/listen, SMTP send
    │   │   └── error-handling.xml                        # Centralized application error handlers
    │   └── resources/
    │       ├── log4j2.xml                                # Asynchronous structured logging configuration
    │       ├── api/
    │       │   └── shipment-tracking.raml                # RAML 1.0 contract (data types, traits, endpoints)
    │       ├── config/
    │       │   ├── mule-dev.yaml                         # Development environment configuration properties
    │       │   └── mule-prod.yaml                        # Production deployment configuration template
    │       ├── dw/
    │       │   ├── bluedart-to-canonical.dwl             # BlueDart flat schema normalizer
    │       │   └── delhivery-to-canonical.dwl            # Delhivery nested schema normalizer
    │       └── examples/
    │           ├── bluedart-event.json                   # Mock BlueDart payload example
    │           ├── delhivery-event.json                  # Mock Delhivery payload example
    │           └── canonical-event.json                  # Mock Canonical lifecycle model example
    └── test/
        ├── munit/
        │   └── shipment-tracking-test-suite.xml          # 9 automated MUnit test suites
        └── resources/
            └── log4j2-test.xml                           # MUnit test execution logging configuration
```

---

## 2. Granular Inventory of All Project Files

### 2.1 Mule Flow Configurations (`src/main/mule/`)

#### 1. `global-config.xml`
- **Exact Path**: `src/main/mule/global-config.xml`
- **Why It Exists**: Houses all shared connector configurations, connection pools, and environment property bindings in one centralized configuration file.
- **What References It**: Every flow in the project references the global configuration names declared here.
- **What It References**: `config/mule-dev.yaml`, `api/shipment-tracking.raml`, and MySQL/VM connector schemas.
- **Execution Role**: Initialized during Mule runtime boot before any HTTP listener starts accepting requests.
- **Failure Impact**: If missing or misconfigured, the application fails to deploy immediately due to unresolvable connector references.

#### 2. `webhook-api.xml`
- **Exact Path**: `src/main/mule/webhook-api.xml`
- **Why It Exists**: Represents the Experience Layer. Hosts the primary HTTP ingress listener (`/api/v1/*`), APIKit Console (`/console/*`), carrier token authentication, and endpoints mapped to RAML.
- **What References It**: Incoming HTTP requests from couriers, enterprise systems, and web browsers.
- **What It References**: `global-config.xml` (HTTP and APIKit configs), `carrier-normalization.xml`, `database-operations.xml`.
- **Execution Role**: First application code to execute upon HTTP ingress.
- **Failure Impact**: Couriers receive HTTP `404 Not Found` or connection refused; no API traffic can enter the system.

#### 3. `carrier-normalization.xml`
- **Exact Path**: `src/main/mule/carrier-normalization.xml`
- **Why It Exists**: Decouples vendor-specific schemas from internal business processing. Evaluates the incoming carrier identity and delegates to dedicated normalizers.
- **What References It**: Invoked by `webhook-api.xml` via `flow-ref name="subflow-route-carrier-normalization"`.
- **What It References**: `dw/bluedart-to-canonical.dwl` and `dw/delhivery-to-canonical.dwl`.
- **Execution Role**: Executes immediately after carrier authentication succeeds.
- **Failure Impact**: Webhooks cannot be parsed into the canonical model; downstream state engine receives raw, unvalidated JSON.

#### 4. `shipment-processing.xml`
- **Exact Path**: `src/main/mule/shipment-processing.xml`
- **Why It Exists**: Houses the core business orchestration logic: deterministic idempotency checks, shipment lookup, quarantine decision for unmanifested packages, and anti-regression state checks.
- **What References It**: Invoked by `webhook-api.xml` after normalization via `flow-ref name="flow-process-canonical-event"`.
- **What It References**: `database-operations.xml`, `risk-assessment.xml`, `notification-queue.xml`.
- **Execution Role**: Core decision-making engine of the application.
- **Failure Impact**: Duplicate events would corrupt audit trails; stale scans would revert delivered shipments back to in-transit.

#### 5. `risk-assessment.xml`
- **Exact Path**: `src/main/mule/risk-assessment.xml`
- **Why It Exists**: The Explainable SLA Risk Engine. Analyzes carrier ETAs against customer promised delivery dates, detects stale transit intervals (>48h), and assigns explainable risk codes.
- **What References It**: Invoked by `shipment-processing.xml` during status forward-progression, and by `webhook-api.xml` for `GET /shipments/{id}/risk`.
- **What It References**: Configuration properties (`risk.staleTransitHours`, `risk.criticalExceptionHours`, `risk.warningLeadHours`).
- **Execution Role**: Executes immediately before persisting shipment master status updates.
- **Failure Impact**: Shipments would lack proactive delay warnings and SLA breach detection.

#### 6. `database-operations.xml`
- **Exact Path**: `src/main/mule/database-operations.xml`
- **Why It Exists**: Represents the System Layer for MySQL. Encapsulates all SQL SELECT, INSERT, and UPDATE queries in isolated, reusable subflows.
- **What References It**: Invoked by `shipment-processing.xml`, `webhook-api.xml`, and `notification-queue.xml`.
- **What It References**: `Database_Config` defined in `global-config.xml`.
- **Execution Role**: Executes whenever durable database reads or writes are required.
- **Failure Impact**: State cannot be persisted or retrieved; application throws `DB:CONNECTIVITY` or `DB:QUERY_EXECUTION`.

#### 7. `notification-queue.xml`
- **Exact Path**: `src/main/mule/notification-queue.xml`
- **Why It Exists**: Manages asynchronous milestone notifications. Evaluates scan eligibility, inserts records into `notification_outbox`, publishes to persistent VM queue, and consumes the queue to send live SMTP emails.
- **What References It**: Producer invoked by `shipment-processing.xml`; consumer driven by `vm:listener`.
- **What It References**: `VM_Config`, `Email_SMTP`, and `database-operations.xml`.
- **Execution Role**: Producer runs synchronously within the webhook transaction; consumer runs asynchronously in a worker thread.
- **Failure Impact**: Webhook responses would block waiting for external email servers, and customers would receive zero milestone alerts.

#### 8. `error-handling.xml`
- **Exact Path**: `src/main/mule/error-handling.xml`
- **Why It Exists**: Houses the centralized `globalError_Handler`. Catches unhandled exceptions, maps them to standard HTTP status codes (`400`, `401`, `404`, `405`, `415`, `503`, `500`), and formats standard JSON error envelopes.
- **What References It**: Referenced by `shipment-tracking-main` (`error-handler ref="globalError_Handler"`).
- **What It References**: System error descriptions and correlation IDs.
- **Execution Role**: Executes only when an error is thrown during request processing.
- **Failure Impact**: Clients receive unformatted, raw HTML error dumps containing internal stack traces.

---

### 2.2 API Specification (`src/main/resources/api/`)

#### 9. `shipment-tracking.raml`
- **Exact Path**: `src/main/resources/api/shipment-tracking.raml`
- **Why It Exists**: The definitive REST contract authored in RAML 1.0. Defines all 12 API resources, methods, query parameters, header requirements, schemas, and status codes.
- **What References It**: Loaded by APIKit Router (`shipment-tracking-config`) and APIKit Console in `global-config.xml`.
- **Execution Role**: Validates incoming HTTP requests before any Mule flow processor executes.
- **Failure Impact**: APIKit router fails to initialize; API contract governance is completely lost.

---

### 2.3 DataWeave Transformations (`src/main/resources/dw/`)

#### 10. `bluedart-to-canonical.dwl`
- **Exact Path**: `src/main/resources/dw/bluedart-to-canonical.dwl`
- **Why It Exists**: Normalizes flat BlueDart webhook payloads (`awb_no`, `status_code`, localized datetime) into the canonical lifecycle event structure.
- **What References It**: Loaded by `carrier-normalization.xml` inside `subflow-normalize-bluedart`.
- **Execution Role**: Executes on BlueDart webhook ingestion.
- **Failure Impact**: BlueDart events cannot be mapped or persisted.

#### 11. `delhivery-to-canonical.dwl`
- **Exact Path**: `src/main/resources/dw/delhivery-to-canonical.dwl`
- **Why It Exists**: Normalizes complex, nested Delhivery payloads (`waybill`, nested `Status.statusCode`, `Scans` array) into the canonical lifecycle event structure.
- **What References It**: Loaded by `carrier-normalization.xml` inside `subflow-normalize-delhivery`.
- **Execution Role**: Executes on Delhivery webhook ingestion.
- **Failure Impact**: Delhivery events cannot be mapped or persisted.

---

### 2.4 Configuration & Environment (`src/main/resources/config/`)

#### 12. `mule-dev.yaml`
- **Exact Path**: `src/main/resources/config/mule-dev.yaml`
- **Why It Exists**: Holds development configuration parameters: HTTP ports (`8081`), MySQL credentials, carrier auth tokens, risk thresholds, and email toggles.
- **What References It**: Loaded by `configuration-properties` in `global-config.xml`.
- **Execution Role**: Loaded into runtime property dictionary at application startup.
- **Failure Impact**: Application fails to deploy due to unresolved `${property}` expressions.

#### 13. `mule-prod.yaml`
- **Exact Path**: `src/main/resources/config/mule-prod.yaml`
- **Why It Exists**: Production deployment template using secure property syntax (`${secure::...}`).
- **What References It**: Used during CloudHub deployments with Anypoint Secure Configuration Properties.
- **Execution Role**: Production environment configuration.
- **Failure Impact**: Production builds lack a template for secure credential injection.

---

### 2.5 Database Scripts (`database/`)

#### 14. `schema.sql`
- **Exact Path**: `database/schema.sql`
- **Why It Exists**: Complete DDL script creating the `shipment_control_tower` database and all 5 tables (`shipments`, `shipment_tracking_events`, `pending_tracking_events`, `notification_outbox`, `integration_alerts`) with foreign keys, constraints, and indexes.
- **What References It**: Executed manually in MySQL Workbench or CLI prior to application startup.
- **Failure Impact**: Database operations throw table/column not found errors.

#### 15. `sample-data.sql`
- **Exact Path**: `database/sample-data.sql`
- **Why It Exists**: Seeds 5 realistic test shipments (`SHP-1001` through `SHP-1005`) covering standard flow, in-transit, delayed SLA, hub arrival, and unmanifested quarantine scenarios.
- **What References It**: Executed during initial setup or before running Postman demo suites.
- **Failure Impact**: Pre-configured test tracking numbers (`BD-987654321`, `DELH-11223344`) do not exist.

#### 16. `verification-queries.sql`
- **Exact Path**: `database/verification-queries.sql`
- **Why It Exists**: Provides safe, non-destructive SELECT statements for judges and evaluators to inspect database records during live demo runs.
- **Failure Impact**: Evaluator cannot quickly verify outbox or idempotency state in MySQL.

---

### 2.6 Testing Suites (`src/test/munit/` & `postman/`)

#### 17. `shipment-tracking-test-suite.xml`
- **Exact Path**: `src/test/munit/shipment-tracking-test-suite.xml`
- **Why It Exists**: Contains 9 automated unit tests verifying BlueDart mapping, Delhivery mapping, auth rejection, duplicate suppression, quarantine handling, SLA risk breach detection, and notification suppression.
- **What References It**: Executed via Maven (`mvn test`) or Anypoint Studio MUnit runner.
- **Failure Impact**: Regressions in DataWeave or routing logic go undetected before deployment.

#### 18. `Shipment-Tracking.postman_collection.json`
- **Exact Path**: `postman/Shipment-Tracking.postman_collection.json`
- **Why It Exists**: Ready-to-import Postman collection containing 16 requests organized into 4 folders (Carrier Ingestion, Shipment Management, Telemetry, and Negative Testing).
- **Failure Impact**: Evaluator must manually construct complex JSON payloads and carrier headers.

---

### 2.7 Build & Logging (`pom.xml`, `mule-artifact.json`, `log4j2.xml`)

#### 19. `pom.xml`
- **Exact Path**: `pom.xml`
- **Why It Exists**: Maven descriptor defining all connector plugins (`mule-http-connector:1.11.3`, `mule-db-connector:1.16.1`, `mule-vm-connector:2.0.1`, `mule-email-connector:1.8.0`, `mule-apikit-module:1.11.3`, MySQL driver `mysql-connector-java:8.0.30`, and MUnit tools).
- **Failure Impact**: Maven cannot resolve dependencies or build the deployable JAR.

#### 20. `log4j2.xml`
- **Exact Path**: `src/main/resources/log4j2.xml`
- **Why It Exists**: Configures asynchronous, non-blocking logging using LMAX Disruptor, formatting log events with correlation IDs and timestamps.
- **Failure Impact**: Console output reverts to default synchronous logging with high I/O overhead.
