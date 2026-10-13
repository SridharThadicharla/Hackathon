# 15 – Logging, Observability & Troubleshooting Guide

**Project**: Shipment Signal Control Tower  
**Logging Framework**: Apache Log4j 2.x (`src/main/resources/log4j2.xml`)  
**Observability Standard**: Distributed Correlation ID Tracing (`X-Correlation-ID`)  

---

## 1. Enterprise Logging Architecture

In high-throughput multi-carrier integration networks, standard debug logging is insufficient. The Control Tower implements structured, asynchronous logging using **Log4j2**:
- **Non-blocking Execution**: Uses `AsyncLogger` and LMAX Disruptor ring buffers to prevent logging I/O from slowing down the HTTP webhook thread.
- **Rolling File Appender**: Rotates log files daily and when file size exceeds `10 MB`, retaining up to 10 historical archives.
- **Contextual Correlation ID Injection**: Injects `%X{correlationId}` into every single log entry automatically.

### 1.1 The Log4j2 Pattern Layout
Configured in `src/main/resources/log4j2.xml`:

```xml
<PatternLayout pattern="%-5p %d [%t] [event: %X{correlationId}] %c: %m%n"/>
```

Example Log Output:
```text
INFO  2026-10-11 11:46:15 [grizzly-http-server-1] [event: c85d8984-9df2-43bb-a53f-a3cf6ad35501] org.mule.runtime.core.internal.processor.LoggerMessageProcessor: [HTTP Ingress] POST /api/v1/webhooks/carriers/BLUEDART | CorrelationId: c85d8984-9df2-43bb-a53f-a3cf6ad35501
INFO  2026-10-11 11:46:15 [grizzly-http-server-1] [event: c85d8984-9df2-43bb-a53f-a3cf6ad35501] org.mule.runtime.core.internal.processor.LoggerMessageProcessor: [Normalizer] BlueDart normalized to Canonical Status: IN_TRANSIT | EventKey: BLUEDART-BD-987654321-IT-20261011103000
INFO  2026-10-11 11:46:15 [grizzly-http-server-1] [event: c85d8984-9df2-43bb-a53f-a3cf6ad35501] org.mule.runtime.core.internal.processor.LoggerMessageProcessor: [Notification Queue] Enqueueing milestone alert for Tracking: BD-987654321 | Milestone: IN_TRANSIT | Queue: shipment-milestone-queue
```

---

## 2. Distributed Tracing with Correlation IDs

Every transaction moving through the control tower carries a unique UUID:
1. **Inbound Header Check**: Checks if the courier submitted an `X-Correlation-ID` header.
2. **Auto-Generation**: If absent, generates a fresh RFC-4122 v4 UUID:
   `vars.correlationId = attributes.headers['x-correlation-id'] default uuid()`
3. **Database Audit Binding**: The correlation ID is saved into `shipment_tracking_events`, `pending_tracking_events`, `notification_outbox`, and `integration_alerts`.
4. **Outbound Header Binding**: Returned in HTTP response headers:
   `X-Correlation-ID: vars.correlationId`
5. **Customer Support Benefit**: If a customer reports a delayed package, support agents can take the `correlationId` from the response and grep all related logs in seconds!

---

## 3. Interpreting Critical Control Tower Log Signals

| Log Marker / Prefix | Severity | Meaning |
|---|---|---|
| `[HTTP Ingress]` | `INFO` | New HTTP webhook received. Displays method, path, and Correlation ID. |
| `[Security]` | `DEBUG/WARN` | Carrier authentication check result. Warns on token mismatch. |
| `[Normalizer]` | `INFO` | Carrier payload normalized to canonical status and event key generated. |
| `[Idempotency]` | `WARN` | Duplicate event key detected. Event safely suppressed. |
| `[Unknown Shipment]` | `WARN` | Unmanifested AWB detected. Event quarantined to pending buffer. |
| `[Out-of-Order]` | `WARN` | Stale scan detected. Recorded in audit history without regressing master state. |
| `[Notification Queue]` | `INFO` | Milestone alert published to persistent asynchronous message queue. |
| `[Notification Consumer]` | `INFO` | Asynchronous worker dispatched alert (SMS/Email) and updated outbox to `SENT`. |

---

## 4. Troubleshooting Playbook: Solutions for Common Problems

### Problem 1: Courier Webhook Returns HTTP 401 Unauthorized
- **Symptom**: Carrier receives `401 Unauthorized` with message `"Missing or invalid carrier authentication credentials"`.
- **Cause**: Missing or incorrect `X-Carrier-Token` header.
- **Fix**: Check `config/mule-dev.yaml`. Ensure the request includes header:
  - BlueDart: `X-Carrier-Token: bluedart-webhook-secret-key-2026`
  - Delhivery: `X-Carrier-Token: delhivery-webhook-secret-key-2026`

---

### Problem 2: Courier Webhook Returns HTTP 400 Unsupported Carrier
- **Symptom**: Returns `400 Bad Request` with code `UNSUPPORTED_CARRIER`.
- **Cause**: URI parameter `{carrierCode}` is not onboarded (e.g. `POST /webhooks/carriers/FEDEX`).
- **Fix**: The router supports `BLUEDART` and `DELHIVERY`. Verify URL spelling: `/webhooks/carriers/BLUEDART`.

---

### Problem 3: Webhook Returns HTTP 503 Database Unavailable
- **Symptom**: Returns `503 Service Unavailable` with code `DATABASE_UNAVAILABLE`.
- **Cause**: MySQL service is stopped or port 3306 is blocked.
- **Fix**: Open PowerShell and check `Get-Service MySQL80`. Run `Start-Service MySQL80`.

---

### Problem 4: MySQL Error "Duplicate entry for key 'uq_events_key'"
- **Symptom**: Raw DB insert errors in console logs.
- **Cause**: Direct SQL execution without the control tower deduplication check.
- **Fix**: In the Mule flow, `subflow-select-event-by-key` intercepts identical keys before `db:insert` executes, ensuring zero raw SQL exceptions.

---

### Problem 5: Out-of-Order Scan Did Not Change Shipment Status
- **Symptom**: You send a `PICKED_UP` scan, but `GET /shipments/{awb}` still shows `IN_TRANSIT`.
- **Explanation**: **This is the expected, correct behavior!** The state progression rule prevents status regression. The scan is recorded in `shipment_tracking_events` for audit history, but the master status is protected from backward regression.
