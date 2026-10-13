# 07 – DataWeave 2.0 & Carrier Mappings Complete Guide

**Project**: Shipment Signal Control Tower  
**Transformation Engine**: MuleSoft DataWeave 2.0  
**Mapping Directory**: `src/main/resources/dw/`  

---

## 1. What is DataWeave 2.0 & Why It Is Used

**DataWeave 2.0** is MuleSoft's native functional expression language specifically designed for high-performance querying and transforming structured data formats (JSON, XML, CSV, Java objects).

In the **Shipment Signal Control Tower**, DataWeave acts as the **Canonical Adapter**:
- Decouples carrier-specific push schemas from internal databases.
- Normalizes disparate date formats and timezones into unified UTC ISO-8601 strings.
- Maps diverse courier status codes into the 9 canonical Use Case 08 lifecycle statuses.
- Generates deterministic composite event keys for deduplication.

---

## 2. The Canonical Lifecycle Event Model

Both BlueDart and Delhivery payloads are normalized into this unified schema:

```json
{
  "eventId": "EVT-BD-20261011103000",
  "eventKey": "BLUEDART-BD-987654321-IT-20261011050000",
  "shipmentId": "SHP-1001",
  "trackingNumber": "BD-987654321",
  "carrier": "BLUEDART",
  "carrierEventCode": "IT",
  "originalStatus": "IT",
  "normalizedStatus": "IN_TRANSIT",
  "eventTimestamp": "2026-10-11T05:00:00Z",
  "receivedTimestamp": "2026-10-11T05:00:05Z",
  "location": "Delhi Regional Processing Hub (DEL/HUB)",
  "description": "In Transit to Destination Delivery Hub",
  "estimatedDeliveryTime": "2026-10-13T12:30:00Z",
  "promisedDeliveryTime": "2026-10-15T18:00:00Z",
  "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501",
  "isDuplicate": false,
  "isOutOfOrder": false,
  "isPendingUnknown": false,
  "sourcePayload": "{...raw json...}"
}
```

---

## 3. Required Canonical Statuses & Mapping Dictionary

| Canonical Status | BlueDart Status Codes | Delhivery Status Values | Business Meaning |
|---|---|---|---|
| `LABEL_CREATED` | `LC`, `BK` | `MANIFESTED`, `MF`, `SOFTDATA UPLOADED` | Manifested, label printed |
| `PICKED_UP` | `PU` | `PENDING`, `PP`, `PICKED UP`, `DISPATCHED` | Physical custody handed to courier |
| `IN_TRANSIT` | `IT`, `DP` | `IN TRANSIT`, `IT` | Movement between transit hubs |
| `ARRIVED_AT_HUB` | `AR`, `HUB` | `BAG IN`, `ARRIVED AT FACILITY` | Scan at sorting/distribution hub |
| `OUT_FOR_DELIVERY` | `OFD`, `OD` | `OUT FOR DELIVERY`, `OFD`, `VAN OUT` | On delivery vehicle for last-mile |
| `DELIVERY_ATTEMPTED`| `UD`, `NA` | `UNDELIVERED`, `DELIVERY ATTEMPTED`, `UD` | Attempted delivery; recipient unavailable |
| `DELIVERED` | `DL`, `OK` | `DELIVERED`, `DL` | Delivery confirmed with OTP/sign |
| `RETURNED` | `RT`, `RTO`, `RDL` | `RTO`, `RETURN TO ORIGIN`, `RETURNED` | Returned back to origin shipper |
| `EXCEPTION` | `EX`, `HLD`, `DMG` | `EXCEPTION`, `EX`, `DAMAGED`, `LOST` | Operational disruption / package damage |
| `UNKNOWN_STATUS` | Any unmapped code | Any unmapped text | Fallback for newly introduced statuses |

---

## 4. BlueDart Normalization (`bluedart-to-canonical.dwl`)

### 4.1 Sample BlueDart Input Payload
```json
{
  "awb_no": "BD-987654321",
  "status_code": "IT",
  "status_description": "In Transit to Destination Hub",
  "scan_date_time": "2026-10-11T10:30:00+05:30",
  "location_code": "DEL/HUB",
  "location_name": "Delhi Central Hub",
  "eta": "2026-10-14T18:00:00+05:30"
}
```

### 4.2 DataWeave Mapping Implementation
```dataweave
%dw 2.0
import try from dw::Runtime
output application/json

// Utility: Converts varying date strings and timezones into UTC ISO-8601
fun toUtcIsoString(val) = 
    if (val == null or (val as String) == "") null
    else do {
        var rawStr = (val as String) replace " " with "T"
        var direct = try(() -> (rawStr as DateTime >> "UTC"))
        var withZ = if (direct.success) direct else try(() -> ((rawStr ++ "Z") as DateTime >> "UTC"))
        var res = if (direct.success) direct.result else if (withZ.success) withZ.result else null
        ---
        if (res != null) res as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"} else null
    }

var rawStatus = upper(trim(payload.status_code default payload.status default "UNKNOWN"))

var normalizedStatusMap = {
    "LC": "LABEL_CREATED", "BK": "LABEL_CREATED",
    "PU": "PICKED_UP",
    "IT": "IN_TRANSIT", "DP": "IN_TRANSIT",
    "AR": "ARRIVED_AT_HUB", "HUB": "ARRIVED_AT_HUB",
    "OFD": "OUT_FOR_DELIVERY", "OD": "OUT_FOR_DELIVERY",
    "UD": "DELIVERY_ATTEMPTED", "NA": "DELIVERY_ATTEMPTED",
    "DL": "DELIVERED", "OK": "DELIVERED",
    "RT": "RETURNED", "RTO": "RETURNED", "RDL": "RETURNED",
    "EX": "EXCEPTION", "HLD": "EXCEPTION", "DMG": "EXCEPTION"
}

var canonicalStatus = normalizedStatusMap[rawStatus] default "UNKNOWN_STATUS"
var rawScanTime = payload.scan_date_time default (now() as String {format: "yyyy-MM-dd'T'HH:mm:ssXXX"})
var eventTimeUtc = toUtcIsoString(rawScanTime) default ((now() >> "UTC") as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"})
var rawEta = payload.eta default null
var etaUtc = toUtcIsoString(rawEta)
var trackingNum = trim(payload.awb_no default payload.tracking_number default "UNKNOWN_AWB")
var compactTs = eventTimeUtc replace /[-:TZ]/ with ""
var eventKeyCalc = "BLUEDART-" ++ trackingNum ++ "-" ++ rawStatus ++ "-" ++ compactTs
---
{
    eventId: payload.event_id default ("EVT-BD-" ++ compactTs),
    eventKey: payload.event_key default eventKeyCalc,
    shipmentId: vars.targetShipmentId default null,
    trackingNumber: trackingNum,
    carrier: "BLUEDART",
    carrierEventCode: rawStatus,
    originalStatus: rawStatus,
    normalizedStatus: canonicalStatus,
    eventTimestamp: eventTimeUtc,
    receivedTimestamp: (now() >> "UTC") as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"},
    location: trim((payload.location_name default "") ++ " (" ++ (payload.location_code default "N/A") ++ ")"),
    description: payload.status_description default ("BlueDart status scan: " ++ rawStatus),
    estimatedDeliveryTime: etaUtc,
    promisedDeliveryTime: vars.promisedDeliveryTime default null,
    correlationId: vars.correlationId default uuid(),
    isDuplicate: false,
    isOutOfOrder: false,
    isPendingUnknown: false,
    sourcePayload: write(payload, "application/json")
}
```

---

## 5. Delhivery Normalization (`delhivery-to-canonical.dwl`)

### 5.1 Sample Delhivery Input Payload
```json
{
  "waybill": "DELH-11223344",
  "Status": {
    "status": "In Transit",
    "statusCode": "IT",
    "statusDateTime": "2026-10-11 11:15:00",
    "instructions": "Departed Bengaluru Sorting Facility"
  },
  "Scans": [
    {
      "scanType": "Bag Out",
      "scanDateTime": "2026-10-11 11:15:00",
      "scannedLocation": "BLR/HUB"
    }
  ],
  "ExpectedDeliveryDate": "2026-10-13T20:00:00Z"
}
```

### 5.2 Key Handling in Delhivery Transformation
- **Nested Status Object**: Safely accesses `payload.Status.statusCode default payload.Status.status`.
- **Space-Separated Timestamps**: Converts `'2026-10-11 11:15:00'` to ISO format by replacing spaces with `'T'`.
- **Scan Array Extraction**: Extracts the latest scan location from `payload.Scans[0].scannedLocation`.
- **Event Key Construction**: Replaces spaces with underscores in raw status:
  `DELHIVERY-DELH-11223344-IT-20261011111500`.

---

## 6. How to Test DataWeave Mappings in Anypoint Studio

1. In Studio Package Explorer, navigate to `src/main/resources/dw/bluedart-to-canonical.dwl`.
2. Double-click to open in the **DataWeave Editor**.
3. In the top-right corner of the editor, click **Preview**.
4. Click **Create required sample data to preview transformation**.
5. Paste the sample BlueDart JSON in the input pane.
6. The output pane immediately renders the real-time normalized canonical JSON!
