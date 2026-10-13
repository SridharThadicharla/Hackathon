# 12 – Error Handling, Resilience & Retry Guide

**Project**: Shipment Signal Control Tower  
**Error Handling Configuration**: `src/main/mule/error-handling.xml`  
**Reliability Patterns**: Circuit Breaker, Exponential Retry, Transactional Outbox, Dead-Letter Queue (DLQ)  

---

## 1. Global Error Handling Strategy

In enterprise logistics, network failures, database connection blips, and carrier schema anomalies are inevitable. The Control Tower implements a deterministic **Global Error Handler** (`globalError_Handler`) utilizing `<on-error-propagate>` to guarantee:
1. Every error produces an RFC-7807 compliant standardized JSON response.
2. Inbound HTTP status codes accurately reflect failure domains (400, 401, 404, 405, 500, 503).
3. The distributed `X-Correlation-ID` is preserved in every error response for rapid triage.
4. Operational alerts are recorded in the `integration_alerts` telemetry table.

```text
                                [Message Flow Execution]
                                           │
                                  [Exception Thrown]
                                           │
                                           ▼
                            [globalError_Handler Dispatcher]
                                           │
     ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
     ▼                  ▼                  ▼                  ▼                  ▼
[APIKIT:BAD_REQUEST] [APP:UNAUTHORIZED] [APIKIT:NOT_FOUND]  [DB:CONNECTIVITY]   [ANY]
  HTTP 400 Bad Req    HTTP 401 Unauth     HTTP 404 Not Found  HTTP 503 DB Fail   HTTP 500
```

---

## 2. Deep-Dive: What Happens During Each Edge-Case Scenario

---

### Scenario A: Database is Unavailable or Unreachable
- **Trigger**: MySQL service is down, network partition between Mule runtime and database cluster, or connection pool exhausted.
- **Mule Exception Type**: `DB:CONNECTIVITY`.
- **System Behavior**:
  1. The MySQL connector's internal retry engine attempts automatic reconnection (`autoReconnect=true`).
  2. If retries fail within `30000ms`, the exception is propagated to `globalError_Handler`.
  3. The error handler sets `vars.httpStatus = 503`.
  4. Returns standardized error response:
     ```json
     {
       "success": false,
       "error": {
         "code": "DATABASE_UNAVAILABLE",
         "message": "Database service is temporarily unavailable or unreachable.",
         "details": "Operational connection to MySQL 8.0 cluster failed. Connection retries exhausted."
       },
       "timestamp": "2026-10-11T06:15:00Z",
       "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501"
     }
     ```
  5. The carrier's webhook dispatcher receives HTTP 503 and schedules a standard backoff retry.

---

### Scenario B: Webhook is Duplicated
- **Trigger**: Carrier resends an identical tracking scan due to network timeout or retry policy.
- **System Behavior**:
  1. Flow constructs deterministic event key: `BLUEDART-BD-987654321-IT-20261011103000`.
  2. Queries `shipment_tracking_events` by `event_key`.
  3. Existing record is found.
  4. Flow sets `vars.isDuplicate = true`.
  5. Suppresses database updates and customer notification generation.
  6. Returns HTTP 200 with `DUPLICATE_ACKNOWLEDGED`:
     ```json
     {
       "success": true,
       "status": "DUPLICATE_ACKNOWLEDGED",
       "message": "Event already processed and recorded. Duplicate delivery suppressed safely.",
       "isDuplicate": true
     }
     ```
  7. Result: Zero redundant DB writes, zero customer notification spam.

---

### Scenario C: Carrier Webhook Arrives with Invalid / Missing Authentication
- **Trigger**: Courier webhook payload missing `X-Carrier-Token` header, or token does not match configured shared secret.
- **Mule Exception Type**: `APP:UNAUTHORIZED`.
- **System Behavior**:
  1. `subflow-validate-carrier-auth` evaluates token match.
  2. If token does not match, logs security warning with masked token.
  3. Raises `APP:UNAUTHORIZED`.
  4. Error handler sets HTTP 401 and returns:
     ```json
     {
       "success": false,
       "error": {
         "code": "UNAUTHORIZED",
         "message": "Missing or invalid carrier authentication credentials.",
         "details": "Provide valid X-Carrier-Token header corresponding to configured carrier shared secret."
       },
       "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501"
     }
     ```

---

### Scenario D: Tracking Scan Arrives for Unmanifested / Unknown Tracking Number
- **Trigger**: Driver scans package at origin hub before WMS order manifestation syncs.
- **System Behavior**:
  1. Query on `shipments` table returns 0 rows.
  2. Flow sets `vars.isPendingUnknown = true`.
  3. Preserves entire raw JSON payload and inserts into `pending_tracking_events` with `processing_status = 'PENDING'`.
  4. Returns HTTP 200 with `QUARANTINED_PENDING_REGISTRATION`:
     ```json
     {
       "success": true,
       "status": "QUARANTINED_PENDING_REGISTRATION",
       "message": "Shipment record not found in master database. Event safely quarantined for auto-reconciliation.",
       "isPendingUnknown": true
     }
     ```
  5. The scan is safely held in quarantine until auto-reconciliation runs.

---

### Scenario E: Carrier Sends an Unmapped / Novel Status Code
- **Trigger**: Courier introduces a new status code (e.g. `CUSTOMS_INSPECTION_HOLD` or `DAMAGED_IN_FLOOD`).
- **System Behavior**:
  1. DataWeave mapping dictionary does not find an exact match.
  2. DataWeave fallback operator `default "UNKNOWN_STATUS"` activates.
  3. The status is recorded in `shipment_tracking_events` as `UNKNOWN_STATUS` along with the original carrier code for audit.
  4. Control tower pulse telemetry increments `unknown_status_events` count for operator review.

---

### Scenario F: Out-of-Order / Stale Tracking Scan
- **Trigger**: Delivery van uploads older transit scan after parcel is already `OUT_FOR_DELIVERY` or `DELIVERED`.
- **System Behavior**:
  1. DataWeave compares incoming timestamp against `last_event_timestamp` and status rank against `status_rank`.
  2. Detects that incoming timestamp is older or rank is lower.
  3. Flow sets `vars.isOutOfOrder = true`.
  4. Inserts row into `shipment_tracking_events` with `processing_result = 'OUT_OF_ORDER_RECORDED'`.
  5. **Does NOT update `shipments` master table** (preserving forward-only progression!).
  6. Returns HTTP 200 with `OUT_OF_ORDER_RECORDED`.

---

## 3. Dead-Letter Queuing (DLQ) & Poison Message Isolation

For asynchronous notifications:
- The persistent queue `shipment-milestone-queue` handles normal alerts.
- If a poison message fails processing repeatedly, it is routed to the Dead-Letter Queue `shipment-milestone-dlq`.
- Operators can inspect DLQ contents and re-drive messages using the `/events/replay` operational endpoint.
