# 10 – DataWeave 2.0 & Carrier Mapping Specifications

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Transformation Engine**: DataWeave 2.0 (Functional, Declarative Transformation Language)  
**Files**: `src/main/resources/dw/bluedart-to-canonical.dwl`, `src/main/resources/dw/delhivery-to-canonical.dwl`  

---

## 1. The Canonical Event Model

To eliminate tight coupling between external courier JSON structures and internal persistence logic, all incoming payloads are transformed into a standardized **Canonical Event Model**:

```json
{
  "eventId": "EVT-BD-20261011103000",
  "eventKey": "BLUEDART-BD-987654321-IT-20261011103000",
  "shipmentId": "SHP-1001",
  "trackingNumber": "BD-987654321",
  "carrier": "BLUEDART",
  "originalStatus": "IT",
  "normalizedStatus": "IN_TRANSIT",
  "eventTimestamp": "2026-10-11T05:00:00Z",
  "receivedTimestamp": "2026-10-11T05:00:02Z",
  "location": "Delhi Regional Sorting Hub",
  "description": "In Transit - Forwarded to Destination Hub",
  "estimatedDeliveryTime": "2026-10-14T12:30:00Z",
  "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501",
  "sourcePayload": "{...}"
}
```

---

## 2. BlueDart Express Normalization (`bluedart-to-canonical.dwl`)

### 2.1 Source vs. Canonical Field Mapping
BlueDart transmits a flat JSON structure with uppercase status abbreviations:

| BlueDart Input Field | Canonical Event Field | Transformation & Normalization Rule |
|---|---|---|
| `payload.awb_no` | `trackingNumber` | Trimmed string. Fallback to `payload.awb` or `"UNKNOWN_AWB"`. |
| Fixed String `"BLUEDART"` | `carrier` | Fixed canonical carrier identifier. |
| `payload.status_code` | `originalStatus` | Raw status preserved for audit compliance. |
| `payload.status_code` | `normalizedStatus` | Evaluated against status dictionary (see table below). |
| `payload.scan_date_time` | `eventTimestamp` | Parsed with `+05:30` offset and shifted to UTC ISO-8601 (`yyyy-MM-dd'T'HH:mm:ss'Z'`). |
| `payload.eta` | `estimatedDeliveryTime` | Parsed with `+05:30` offset and shifted to UTC. |
| `payload.location_name` | `location` | Concatenates `location_code` and `location_name`. |
| Composite Expression | `eventKey` | `"BLUEDART-" ++ trackingNumber ++ "-" ++ originalStatus ++ "-" ++ cleanTimestamp` |

### 2.2 BlueDart Status Code Dictionary
```dataweave
var normalizedStatusMap = {
    "MF": "LABEL_CREATED",
    "MANIFESTED": "LABEL_CREATED",
    "PU": "PICKED_UP",
    "PICKED_UP": "PICKED_UP",
    "IT": "IN_TRANSIT",
    "IN_TRANSIT": "IN_TRANSIT",
    "OFD": "OUT_FOR_DELIVERY",
    "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
    "UD": "DELIVERY_ATTEMPTED",
    "DELIVERY_ATTEMPTED": "DELIVERY_ATTEMPTED",
    "DL": "DELIVERED",
    "DELIVERED": "DELIVERED",
    "RT": "RETURNED",
    "RETURNED": "RETURNED",
    "EX": "EXCEPTION",
    "EXCEPTION": "EXCEPTION"
}
```

### 2.3 Date/Time Normalization Function
```dataweave
fun toUtcIsoString(dtStr) = 
    if (dtStr == null or dtStr == "") null
    else do {
        var withT = dtStr replace " " with "T"
        var withOffset = if (withT contains "+") withT else withT ++ "+05:30"
        ---
        (withOffset as DateTime >> "UTC") as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"}
    }
```
- **Why It Matters**: BlueDart sends scan times in Indian Standard Time (IST, UTC+5:30). Converting every timestamp to UTC at ingestion ensures all calculations in the risk engine and database queries operate on identical timezone baselines.

---

## 3. Delhivery Logistics Normalization (`delhivery-to-canonical.dwl`)

### 3.1 Source vs. Canonical Field Mapping
Delhivery transmits a deeply nested structure containing dynamic scan arrays:

| Delhivery Input Field | Canonical Event Field | Transformation & Normalization Rule |
|---|---|---|
| `payload.waybill` | `trackingNumber` | Trimmed string. Fallback to `payload.tracking_number`. |
| Fixed String `"DELHIVERY"` | `carrier` | Fixed canonical carrier identifier. |
| `payload.Status.statusCode` | `originalStatus` | Falls back to `Status.status` or `payload.status`. |
| `payload.Status.statusCode` | `normalizedStatus` | Evaluated against Delhivery status dictionary. |
| `Status.statusDateTime` | `eventTimestamp` | If absent, falls back to `Scans[0].scanDateTime`. Converted to UTC. |
| `ExpectedDeliveryDate` | `estimatedDeliveryTime` | Converted to UTC ISO-8601 string. |
| `Scans[0].scannedLocation` | `location` | Extracted from the most recent scan in `Scans` array. |
| Composite Expression | `eventKey` | `"DELHIVERY-" ++ trackingNumber ++ "-" ++ rawStatus ++ "-" ++ cleanTimestamp` |

### 3.2 Delhivery Status Code Dictionary
```dataweave
var normalizedStatusMap = {
    "MANIFESTED": "LABEL_CREATED",
    "SOFTDATA UPLOADED": "LABEL_CREATED",
    "PENDING": "PICKED_UP",
    "PP": "PICKED_UP",
    "PICKED UP": "PICKED_UP",
    "DISPATCHED": "IN_TRANSIT",
    "IN TRANSIT": "IN_TRANSIT",
    "BAG IN": "ARRIVED_AT_HUB",
    "ARRIVED AT FACILITY": "ARRIVED_AT_HUB",
    "OUT FOR DELIVERY": "OUT_FOR_DELIVERY",
    "OFD": "OUT_FOR_DELIVERY",
    "VAN OUT": "OUT_FOR_DELIVERY",
    "UNDELIVERED": "DELIVERY_ATTEMPTED",
    "DELIVERY ATTEMPTED": "DELIVERY_ATTEMPTED",
    "DELIVERED": "DELIVERED",
    "DL": "DELIVERED",
    "RTO": "RETURNED",
    "RETURN TO ORIGIN": "RETURNED",
    "DAMAGED": "EXCEPTION",
    "LOST": "EXCEPTION"
}
```

---

## 4. Deterministic EventKey Construction Explained

To enforce deduplication without relying on carrier-generated event IDs (which are frequently absent or reused), both DataWeave transformations synthesize a **deterministic composite `eventKey`**:

```text
Format: <CARRIER>-<TRACKING_NUMBER>-<ORIGINAL_STATUS>-<YYYYMMDDHHMMSS>
Example 1: BLUEDART-BD-987654321-IT-20261011103000
Example 2: DELHIVERY-DELH-11223344-OFD-20261011083000
```

### Why This Format Was Selected:
1. **Mathematical Uniqueness**: Two physical scans for the same package at the same second with the same status are guaranteed to produce the exact same key.
2. **Deterministic Regeneration**: If a carrier resends the same webhook 5 minutes later due to a network timeout, the generated `eventKey` is 100% identical.
3. **Database Guard**: Mapped directly to the MySQL column `event_key` which is indexed by a `UNIQUE KEY` constraint.
