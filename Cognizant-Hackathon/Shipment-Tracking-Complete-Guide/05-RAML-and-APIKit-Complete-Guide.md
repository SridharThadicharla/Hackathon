# 05 – RAML 1.0 & APIKit Complete Guide

**Project**: Shipment Signal Control Tower  
**API Specification**: RAML 1.0 (`src/main/resources/api/shipment-tracking.raml`)  
**Router Module**: MuleSoft APIKit Module (`mule-apikit-module:1.11.3`)  

---

## 1. What is RAML 1.0 & Why It Is Used

**RAML (RESTful API Modeling Language)** is an open, YAML-based modeling language designed to describe RESTful APIs clearly. In MuleSoft development:
1. **Contract-First Design**: The API contract is authored, validated, and approved before writing implementation code.
2. **Automated Request Validation**: The Mule APIKit Router validates incoming HTTP requests, headers, query parameters, and JSON payloads against the RAML contract automatically.
3. **Automated Flow Generation**: Anypoint Studio automatically scaffolds Mule flows named after the RAML resources and HTTP methods.

---

## 2. APIKit Router Configuration in Mule 4

The APIKit router is configured in `src/main/mule/global-config.xml`:

```xml
<apikit:config 
    name="shipment-tracking-config" 
    raml="api/shipment-tracking.raml" 
    outboundHeadersMapName="outboundHeaders" 
    httpStatusVarName="httpStatus" 
    doc:name="Router" />
```

And invoked in `src/main/mule/webhook-api.xml` inside `shipment-tracking-main`:

```xml
<flow name="shipment-tracking-main">
    <http:listener config-ref="HTTP_Listener_config" path="/api/v1/*">
        <http:response statusCode="#[vars.httpStatus default 200]">
            <http:headers><![CDATA[#[{
                "X-Correlation-ID": vars.correlationId default uuid(),
                "Content-Type": "application/json"
            }]]]></http:headers>
        </http:response>
    </http:listener>

    <set-variable variableName="correlationId" 
        value="#[attributes.headers['x-correlation-id'] default attributes.headers['X-Correlation-ID'] default uuid()]" />

    <apikit:router config-ref="shipment-tracking-config" />
    <error-handler ref="globalError_Handler" />
</flow>
```

---

## 3. Implemented RAML Resources & Flow Mapping

Every resource and method defined in `shipment-tracking.raml` maps to an implementation flow in `src/main/mule/webhook-api.xml`:

| RAML Resource & Method | APIKit Flow Name in `webhook-api.xml` | Purpose |
|---|---|---|
| `POST /webhooks/carriers/{carrierCode}` | `post:\webhooks\carriers\(carrierCode):application\json:shipment-tracking-config` | Multi-carrier webhook ingestion |
| `POST /webhooks/bluedart` | `post:\webhooks\bluedart:application\json:shipment-tracking-config` | Direct BlueDart webhook ingestion |
| `POST /webhooks/delhivery` | `post:\webhooks\delhivery:application\json:shipment-tracking-config` | Direct Delhivery webhook ingestion |
| `POST /shipments` | `post:\shipments:application\json:shipment-tracking-config` | Register new shipment master in DB |
| `GET /shipments/{trackingNumber}` | `get:\shipments\(trackingNumber):shipment-tracking-config` | Fetch latest shipment state & SLA status |
| `GET /shipments/{trackingNumber}/history` | `get:\shipments\(trackingNumber)\history:shipment-tracking-config` | Fetch full chronological audit event trail |
| `GET /shipments/{trackingNumber}/risk` | `get:\shipments\(trackingNumber)\risk:shipment-tracking-config` | Compute explainable SLA delay risk |
| `GET /health` | `get:\health:shipment-tracking-config` | Operational health check (DB & Queue) |
| `GET /carriers/pulse` | `get:\carriers\pulse:shipment-tracking-config` | Telemetry & aggregated carrier metrics |
| `POST /events/replay` | `post:\events\replay:application\json:shipment-tracking-config` | Operator replay of quarantined events |
| `POST /events/reconcile` | `post:\events\reconcile:shipment-tracking-config` | Batch auto-reconcile of pending events |

---

## 4. RAML Data Types Deep-Dive

### 4.1 WebhookAcknowledgment
Returned to couriers after webhook evaluation:
```yaml
WebhookAcknowledgment:
  type: object
  properties:
    success: boolean
    status: string               # EVENT_PROCESSED_SUCCESSFULLY, DUPLICATE_ACKNOWLEDGED, OUT_OF_ORDER_RECORDED, QUARANTINED_PENDING_REGISTRATION
    message: string
    eventId?: string
    shipmentId?: string
    trackingNumber?: string
    carrier?: string
    normalizedStatus?: string
    isDuplicate: boolean
    isOutOfOrder: boolean
    isPendingUnknown: boolean
    receivedTimestamp: datetime
    correlationId: string
```

### 4.2 RiskAssessment
Computed dynamically by comparing carrier ETAs against promised SLAs:
```yaml
RiskAssessment:
  type: object
  properties:
    shipmentId: string
    trackingNumber: string
    carrier: string
    currentStatus: string
    riskLevel:
      enum: [ON_TRACK, AT_RISK, DELAYED, CRITICAL, UNKNOWN]
    reasonCode: string
    explanation: string
    evaluatedAt: datetime
    estimatedDeliveryTime?: datetime
    promisedDeliveryTime?: datetime
    lastEventTimestamp?: datetime
    riskFactors:
      type: array
      items: string
```

### 4.3 Standard Error Contract (RFC-7807 Aligned)
Standard error structure returned on validation or runtime errors:
```yaml
ErrorResponse:
  type: object
  properties:
    success: boolean
    error:
      type: object
      properties:
        code: string
        message: string
        details?: string
    timestamp: datetime
    correlationId: string
```

---

## 5. Security Traits & Header Handling

In `shipment-tracking.raml`, the `carrierSecured` trait enforces token headers:
```yaml
traits:
  carrierSecured:
    headers:
      X-Carrier-Token:
        type: string
        description: Carrier authentication token / shared secret
        required: false
      X-Correlation-ID:
        type: string
        description: Distributed correlation ID for tracing
        required: false
```
The Mule subflow `subflow-validate-carrier-auth` checks that the incoming `X-Carrier-Token` header matches the carrier's configured secret in `config/mule-dev.yaml`. If missing or invalid, an `APP:UNAUTHORIZED` exception is thrown, which the global error handler translates to HTTP `401 Unauthorized`.
