# 05 – RAML 1.0 Specification & APIKit Routing

**Specification File**: `src/main/resources/api/shipment-tracking.raml`  
**Specification Standard**: RAML 1.0 (RESTful API Modeling Language)  
**API Title**: Shipment Signal Control Tower API  
**API Version**: v1  
**Base URI**: `http://localhost:8081/api/v1`  
**Media Type**: `application/json`  

---

## 1. Contract-First API Design in MuleSoft

**Contract-First Design** means authoring and finalizing the API specification (RAML) *before* writing any integration code.

In MuleSoft development, this provides three enterprise advantages:
1. **Automated Request Validation**: The Mule APIKit Router validates incoming HTTP requests, headers, query parameters, and JSON payloads against the RAML contract automatically. Invalid payloads receive an immediate `400 Bad Request` without executing flow logic.
2. **Automated Flow Scaffolding**: Anypoint Studio automatically scaffolds Mule flows named after the RAML resources and HTTP methods.
3. **Interactive Documentation**: The specification automatically renders an interactive APIKit Console at `http://localhost:8081/console/`.

---

## 2. Reusable Data Types & Security Traits

### 2.1 Reusable Data Types (`types:`)

| RAML Data Type | Purpose & Structure | Key Properties |
|---|---|---|
| **`WebhookAcknowledgment`** | Response returned to courier systems after webhook evaluation. | `success` (boolean), `status` (string), `message` (string), `isDuplicate` (boolean), `isOutOfOrder` (boolean), `isPendingUnknown` (boolean), `correlationId` (string). |
| **`ShipmentDetail`** | Master view of a shipment record from the database. | `shipmentId`, `trackingNumber`, `carrier`, `originLocation`, `destinationLocation`, `currentStatus`, `statusRank`, `estimatedDeliveryTime`, `promisedDeliveryTime`, `riskLevel`, `riskReason`. |
| **`ShipmentEvent`** | Audit trail entry representing a single physical scan. | `id`, `eventKey`, `shipmentId`, `trackingNumber`, `carrier`, `originalStatus`, `normalizedStatus`, `eventTimestamp`, `receivedTimestamp`, `location`. |
| **`RiskAssessment`** | Explainable delivery delay calculation against promised SLA. | `shipmentId`, `trackingNumber`, `riskLevel` (`ON_TRACK`, `AT_RISK`, `DELAYED`), `reasonCode` (`PROMISED_SLA_BREACHED`, `STALE_TRANSIT`), `etaDifferenceHours`, `explanation`. |
| **`HealthStatus`** | Operational readiness response. | `status` (`UP`), `service`, `version`, `database` (`CONNECTED`), `queue` (`CONNECTED`), `timestamp`. |
| **`CarrierPulseMetrics`** | Aggregated telemetry per courier partner. | `carrier`, `totalEventsReceived`, `successfullyProcessed`, `duplicateEvents`, `outOfOrderEvents`, `pendingUnknownShipments`, `healthStatus`. |
| **`ErrorResponse`** | Standardized error envelope for all failures. | `success: false`, `error: { code, message, details }`, `timestamp`, `correlationId`. |

### 2.2 Security Traits (`traits:`)

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
        description: Distributed correlation ID for end-to-end transaction tracing
        required: false
```

---

## 3. Comprehensive Resource-to-Flow Mapping Table

Every resource and HTTP method defined in [shipment-tracking.raml](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/resources/api/shipment-tracking.raml) maps to a corresponding flow in [webhook-api.xml](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/mule/webhook-api.xml):

| RAML Resource Path | HTTP Method | APIKit Flow Name in `webhook-api.xml` | Purpose & Behavior | Implementation Status |
|---|---|---|---|---|
| `/webhooks/carriers/{carrierCode}` | `POST` | `post:\webhooks\carriers\(carrierCode):application\json:shipment-tracking-config` | Multi-carrier ingestion gateway. Parameterized route handling any registered courier. | **IMPLEMENTED AND VERIFIED** |
| `/webhooks/bluedart` | `POST` | `post:\webhooks\bluedart:application\json:shipment-tracking-config` | Dedicated direct route for BlueDart Express webhooks. | **IMPLEMENTED AND VERIFIED** |
| `/webhooks/delhivery` | `POST` | `post:\webhooks\delhivery:application\json:shipment-tracking-config` | Dedicated direct route for Delhivery Logistics webhooks. | **IMPLEMENTED AND VERIFIED** |
| `/shipments` | `POST` | `post:\shipments:application\json:shipment-tracking-config` | Registers a new master shipment from WMS/TMS into MySQL (`201 Created`). | **IMPLEMENTED AND VERIFIED** |
| `/shipments/{trackingNumber}` | `GET` | `get:\shipments\(trackingNumber):shipment-tracking-config` | Retrieves current status, SLA dates, and latest risk score. | **IMPLEMENTED AND VERIFIED** |
| `/shipments/{trackingNumber}/history` | `GET` | `get:\shipments\(trackingNumber)\history:shipment-tracking-config` | Retrieves full chronological audit event trail. | **IMPLEMENTED AND VERIFIED** |
| `/shipments/{trackingNumber}/risk` | `GET` | `get:\shipments\(trackingNumber)\risk:shipment-tracking-config` | Executes real-time Explainable Risk Engine for given shipment. | **IMPLEMENTED AND VERIFIED** |
| `/shipments/{trackingNumber}/notifications` | `GET` | `get:\shipments\(trackingNumber)\notifications:shipment-tracking-config` | Retrieves dispatched customer alerts from transactional outbox table. | **IMPLEMENTED AND VERIFIED** |
| `/health` | `GET` | `get:\health:shipment-tracking-config` | Operational health check probing database and queue connectivity. | **IMPLEMENTED AND VERIFIED** |
| `/carriers/pulse` | `GET` | `get:\carriers\pulse:shipment-tracking-config` | Aggregated telemetry & volume anomaly metrics across couriers. | **IMPLEMENTED AND VERIFIED** |
| `/events/replay` | `POST` | `post:\events\replay:application\json:shipment-tracking-config` | Operator endpoint to manually reprocess quarantined events. | **IMPLEMENTED AND VERIFIED** |
| `/events/reconcile` | `POST` | `post:\events\reconcile:shipment-tracking-config` | Batch auto-reconciliation of quarantined events for newly registered parcels. | **IMPLEMENTED AND VERIFIED** |

---

## 4. How APIKit Router Uses the Specification

In [src/main/mule/global-config.xml](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/mule/global-config.xml):
```xml
<apikit:config 
    name="shipment-tracking-config" 
    raml="api/shipment-tracking.raml" 
    outboundHeadersMapName="outboundHeaders" 
    httpStatusVarName="httpStatus" 
    doc:name="Router" />
```

And in [src/main/mule/webhook-api.xml](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/mule/webhook-api.xml):
```xml
<flow name="shipment-tracking-main" doc:id="flow-api-main">
    <http:listener config-ref="HTTP_Listener_config" path="/api/v1/*" doc:name="Ingress HTTP Listener" />
    <apikit:router config-ref="shipment-tracking-config" doc:name="APIKit Router" />
    <error-handler ref="globalError_Handler" />
</flow>
```

### Execution Behavior:
1. When an HTTP request enters `/api/v1/*`, `apikit:router` matches the URI path and HTTP method against `shipment-tracking.raml`.
2. If the request matches a valid resource, APIKit delegates execution to the matching flow (e.g., `post:\webhooks\carriers\(carrierCode)...`).
3. If an invalid method is used (e.g., `DELETE /shipments/123`), APIKit throws `APIKIT:METHOD_NOT_ALLOWED` (`405`).
4. If an unknown URL path is requested, APIKit throws `APIKIT:NOT_FOUND` (`404`).
5. If invalid JSON is sent, APIKit throws `APIKIT:BAD_REQUEST` (`400`).

---

## 5. Interview Questions & Model Answers

### Q1: What is the benefit of using RAML 1.0 with MuleSoft APIKit?
**Interview-Ready Answer**:  
*"RAML 1.0 enforces contract-first API design. The APIKit Router automatically handles request routing, schema validation, and error generation before any downstream flow executes. This guarantees that malformed requests are rejected at the edge, protecting our business logic and database from bad data."*

### Q2: Did your implementation match the RAML contract 100%?
**Interview-Ready Answer**:  
*"Yes, 100% of the 12 resources and methods specified in `shipment-tracking.raml` have corresponding implementation flows in `webhook-api.xml`. All data types—including `WebhookAcknowledgment`, `ShipmentDetail`, and `RiskAssessment`—are returned with exact field compliance."*
