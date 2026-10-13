# 08 – Granular Flow-by-Flow Technical Reference

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0)  

---

## Master Flow Index

| Flow / Subflow Name | Source XML File | Execution Type | Primary Responsibility |
|---|---|---|---|
| `shipment-tracking-main` | `webhook-api.xml` | Listener-driven (Sync) | HTTP Ingress router (`/api/v1/*`), correlation ID extraction, APIKit routing. |
| `shipment-tracking-console` | `webhook-api.xml` | Listener-driven (Sync) | APIKit interactive console endpoint (`/console/*`). |
| `subflow-validate-carrier-auth` | `webhook-api.xml` | Subflow (Sync) | Validates `X-Carrier-Token` header against carrier shared secrets. |
| `post:\webhooks\carriers\(carrierCode)...` | `webhook-api.xml` | APIKit Flow (Sync) | Parameterized webhook ingestion route for any carrier. |
| `post:\webhooks\bluedart...` | `webhook-api.xml` | APIKit Flow (Sync) | Dedicated BlueDart webhook ingestion route. |
| `post:\webhooks\delhivery...` | `webhook-api.xml` | APIKit Flow (Sync) | Dedicated Delhivery webhook ingestion route. |
| `post:\shipments...` | `webhook-api.xml` | APIKit Flow (Sync) | WMS master shipment registration (`201 Created`). |
| `get:\shipments\(trackingNumber)...` | `webhook-api.xml` | APIKit Flow (Sync) | Retrieves latest master status and SLA info. |
| `get:\shipments\(trackingNumber)\history...` | `webhook-api.xml` | APIKit Flow (Sync) | Retrieves full chronological audit trail of scans. |
| `get:\shipments\(trackingNumber)\risk...` | `webhook-api.xml` | APIKit Flow (Sync) | Evaluates and returns explainable SLA risk score. |
| `get:\shipments\(trackingNumber)\notifications...` | `webhook-api.xml` | APIKit Flow (Sync) | Retrieves customer alerts from `notification_outbox`. |
| `get:\health...` | `webhook-api.xml` | APIKit Flow (Sync) | Health check probing MySQL and VM queues. |
| `get:\carriers\pulse...` | `webhook-api.xml` | APIKit Flow (Sync) | Aggregated carrier telemetry & anomaly metrics. |
| `post:\events\replay...` | `webhook-api.xml` | APIKit Flow (Sync) | Operator replay of quarantined events. |
| `post:\events\reconcile...` | `webhook-api.xml` | APIKit Flow (Sync) | Batch reconciliation of pending quarantined events. |
| `subflow-route-carrier-normalization` | `carrier-normalization.xml` | Subflow (Sync) | Carrier routing choice router. |
| `subflow-normalize-bluedart` | `carrier-normalization.xml` | Subflow (Sync) | Transforms BlueDart flat JSON to canonical model. |
| `subflow-normalize-delhivery` | `carrier-normalization.xml` | Subflow (Sync) | Transforms Delhivery nested JSON to canonical model. |
| `flow-process-canonical-event` | `shipment-processing.xml` | Flow (Sync) | Idempotency, quarantine, anti-regression, and dispatch. |
| `subflow-evaluate-eta-and-delay` | `risk-assessment.xml` | Subflow (Sync) | Explainable SLA Risk Engine calculation. |
| `subflow-check-duplicate-event` | `database-operations.xml` | Subflow (Sync) | Queries `shipment_tracking_events` by `event_key`. |
| `subflow-lookup-shipment-by-tracking` | `database-operations.xml` | Subflow (Sync) | Queries `shipments` by `tracking_number`. |
| `subflow-select-shipment-by-id` | `database-operations.xml` | Subflow (Sync) | Queries `shipments` by ID or tracking number. |
| `subflow-select-events-by-shipment-id` | `database-operations.xml` | Subflow (Sync) | Queries event history ordered by timestamp. |
| `subflow-quarantine-unknown-shipment` | `database-operations.xml` | Subflow (Sync) | Inserts unmanifested scan into `pending_tracking_events`. |
| `subflow-insert-tracking-event` | `database-operations.xml` | Subflow (Sync) | Inserts audit record into `shipment_tracking_events`. |
| `subflow-update-shipment-status-and-event` | `database-operations.xml` | Subflow (Sync) | Transactional master update + event history insert. |
| `subflow-insert-notification-outbox` | `database-operations.xml` | Subflow (Sync) | Inserts outbox record (`status = 'QUEUED'`). |
| `subflow-mark-notification-sent` | `database-operations.xml` | Subflow (Sync) | Updates outbox record (`status = 'SENT'`). |
| `subflow-publish-milestone-notification` | `notification-queue.xml` | Subflow (Sync) | Milestone filter, outbox persistence, and VM publish. |
| `flow-consume-milestone-notification` | `notification-queue.xml` | Listener (Async) | VM listener, HTML rendering, SMTP send, outbox update. |
| `globalError_Handler` | `error-handling.xml` | Error Handler | Centralized mapping of Mule exceptions to HTTP errors. |

---

## 1. Experience Layer Flows (`webhook-api.xml`)

### Flow 1.1: `shipment-tracking-main`
- **File**: `src/main/mule/webhook-api.xml`
- **Type**: Listener-driven, Synchronous.
- **Business Purpose**: Entry point for all HTTP traffic hitting `/api/v1/*`. Initializes distributed transaction context and routes to APIKit.
- **How Reached**: Inbound HTTP POST/GET from couriers or clients.
- **Input**: HTTP request body, query params, headers (`X-Correlation-ID`).
- **Processors in Execution Order**:
  1. `<http:listener config-ref="HTTP_Listener_config" path="/api/v1/*">`: Listens on port 8081. Formats response headers with `X-Correlation-ID` and `Content-Type: application/json`.
  2. `<set-variable variableName="correlationId">`: Extracts client correlation ID or generates `uuid()`.
  3. `<logger>`: Logs method, request path, and correlation ID.
  4. `<apikit:router config-ref="shipment-tracking-config">`: Evaluates request against `api/shipment-tracking.raml`.
- **Output**: Synchronous response constructed by downstream flow.
- **Error Handling**: Delegates to `globalError_Handler`.
- **Interview Answer (25s)**: *"The `shipment-tracking-main` flow is our HTTP ingress gateway. It extracts or generates a distributed correlation ID for end-to-end tracing, logs the transaction, and hands the request to the APIKit Router to validate headers, parameters, and bodies against our RAML 1.0 contract."*

---

### Flow 1.2: `subflow-validate-carrier-auth`
- **File**: `src/main/mule/webhook-api.xml`
- **Type**: Synchronous Subflow.
- **Business Purpose**: Enforces edge security for carrier webhooks.
- **Input**: `attributes.headers['x-carrier-token']`, `vars.carrier`.
- **Processors**:
  1. `<set-variable variableName="inboundToken">`: Extracts token from header or query parameter.
  2. `<choice>`: Verifies if BlueDart token equals `p('carrier.bluedart.token')` or Delhivery token equals `p('carrier.delhivery.token')`.
  3. `<raise-error type="APP:UNAUTHORIZED">`: Thrown if token does not match.
- **Output**: Returns cleanly if authorized; halts with HTTP 401 if invalid.
- **Related MUnit Tests**: `test-unauthorized-carrier-token-rejection`, `test-authorized-carrier-token-success`.

---

### Flow 1.3: `post:\webhooks\carriers\(carrierCode):application\json:shipment-tracking-config`
- **File**: `src/main/mule/webhook-api.xml`
- **Type**: APIKit Routing Flow.
- **Business Purpose**: Core parameterized ingestion endpoint for multi-carrier webhooks.
- **Processors**:
  1. `<set-variable variableName="carrier">`: Extracts `carrierCode` URI parameter in uppercase (`BLUEDART`, `DELHIVERY`).
  2. `<flow-ref name="subflow-validate-carrier-auth">`: Validates security token.
  3. `<flow-ref name="subflow-route-carrier-normalization">`: Normalizes vendor JSON.
  4. `<flow-ref name="flow-process-canonical-event">`: Processes business logic.
- **Output**: `WebhookAcknowledgment` JSON response (`HTTP 200 OK`).

---

## 2. Normalization Layer Flows (`carrier-normalization.xml`)

### Flow 2.1: `subflow-normalize-bluedart`
- **File**: `src/main/mule/carrier-normalization.xml`
- **Business Purpose**: Maps flat BlueDart JSON (`awb_no`, `status_code`, localized datetime) to canonical lifecycle model.
- **Key Expression**: Invokes [src/main/resources/dw/bluedart-to-canonical.dwl](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/resources/dw/bluedart-to-canonical.dwl).
- **Variables Created**:
  - `vars.canonicalEvent`: Normalized event object.
  - `payload`: Set to `vars.canonicalEvent`.
- **Related MUnit Tests**: `test-valid-bluedart-event-normalization`, `test-unknown-carrier-status-normalization`.

---

### Flow 2.2: `subflow-normalize-delhivery`
- **File**: `src/main/mule/carrier-normalization.xml`
- **Business Purpose**: Maps complex Delhivery nested JSON (`waybill`, `Status`, `Scans` array) to canonical lifecycle model.
- **Key Expression**: Invokes [src/main/resources/dw/delhivery-to-canonical.dwl](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/resources/dw/delhivery-to-canonical.dwl).
- **Variables Created**: `vars.canonicalEvent`.
- **Related MUnit Test**: `test-valid-delhivery-event-normalization`.

---

## 3. Core Processing Flows (`shipment-processing.xml`)

### Flow 3.1: `flow-process-canonical-event`
- **File**: `src/main/mule/shipment-processing.xml`
- **Type**: Synchronous Flow.
- **Business Purpose**: The central business intelligence and orchestration hub.
- **Execution Steps**:
  1. **Idempotency Check**: Calls `subflow-check-duplicate-event`. If `sizeOf(existingEvent) > 0`, sets `vars.isDuplicate = true`, skips database mutation, and returns `status: "DUPLICATE_ACKNOWLEDGED"`.
  2. **Shipment Lookup**: Calls `subflow-lookup-shipment-by-tracking`. If not found, calls `subflow-quarantine-unknown-shipment` and returns `status: "QUARANTINED_PENDING_REGISTRATION"`.
  3. **Anti-Regression Check**: Evaluates numeric status rank and timestamps. If incoming event is stale or received after terminal state, sets `isOutOfOrder = true`, writes audit row via `subflow-insert-tracking-event` without regressing shipment master state, and returns `status: "OUT_OF_ORDER_RECORDED"`.
  4. **Risk Evaluation & State Progression**: For valid forward progression:
     - Invokes `subflow-evaluate-eta-and-delay` to compute SLA risk.
     - Invokes `subflow-update-shipment-status-and-event` to update `shipments` master and append `shipment_tracking_events`.
     - Invokes `subflow-publish-milestone-notification` to queue customer alert.
     - Returns `status: "EVENT_PROCESSED_SUCCESSFULLY"`.
- **Related MUnit Tests**: `test-duplicate-event-detection-and-suppression`, `test-unknown-shipment-quarantining`.

---

## 4. Explainable Risk Engine (`risk-assessment.xml`)

### Flow 4.1: `subflow-evaluate-eta-and-delay`
- **File**: `src/main/mule/risk-assessment.xml`
- **Business Purpose**: Analyzes carrier ETAs against promised SLAs to assign transparent, explainable delay risks.
- **Logic Rules**:
  - `incomingTs > promisedDt` $\rightarrow$ `DELAYED` / `PROMISED_SLA_BREACHED`.
  - `lastEventTimestamp` > 48 hours ago $\rightarrow$ `AT_RISK` / `STALE_TRANSIT`.
  - `etaDifferenceHours > 24` $\rightarrow$ `DELAYED` / `CRITICAL_DELAY`.
  - `etaDifferenceHours > 6` $\rightarrow$ `AT_RISK` / `SLA_BREACH_WARNING`.
  - Otherwise $\rightarrow$ `ON_TRACK`.
- **Variables Created**: `vars.riskAssessment` containing `riskLevel`, `reasonCode`, `etaDifferenceHours`, and `explanation`.
- **Related MUnit Test**: `test-risk-evaluation-delayed-sla`.

---

## 5. Notification & Queue Flows (`notification-queue.xml`)

### Flow 5.1: `subflow-publish-milestone-notification`
- **File**: `src/main/mule/notification-queue.xml`
- **Type**: Synchronous Subflow.
- **Business Purpose**: Milestone filter and transactional outbox publisher.
- **Eligibility Filter**: Status must be in `['PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'EXCEPTION', 'DELIVERY_ATTEMPTED']`, not duplicate, not out-of-order, and not quarantined.
- **Actions**:
  1. Builds `notificationPayload`.
  2. Calls `subflow-insert-notification-outbox` to persist record in MySQL (`status: 'QUEUED'`).
  3. Publishes message to `<vm:publish config-ref="VM_Config" queueName="shipment-milestone-queue">`.
  4. If non-milestone (e.g., `IN_TRANSIT`), logs suppression by design and skips enqueueing.
- **Related MUnit Test**: `test-notification-milestone-filtering`.

---

### Flow 5.2: `flow-consume-milestone-notification`
- **File**: `src/main/mule/notification-queue.xml`
- **Type**: Asynchronous Listener-driven Flow.
- **Business Purpose**: Consumes milestone events from VM queue and dispatches physical/simulated email alerts.
- **Component**: `<vm:listener config-ref="VM_Config" queueName="shipment-milestone-queue">`.
- **Actions**:
  1. Reads `notificationItem` from payload.
  2. Renders styled HTML card template.
  3. Checks `p('notification.email.enabled') == 'true'`:
     - If true: Dispatches email via `<email:send config-ref="Email_SMTP">` (STARTTLS port 587). Handled with `on-error-continue` to log SMTP network errors gracefully without crashing the queue.
     - If false: Logs full email simulation in Studio console.
  4. Calls `subflow-mark-notification-sent` to update `notification_outbox` status to `'SENT'` and `sent_at = NOW()`.
