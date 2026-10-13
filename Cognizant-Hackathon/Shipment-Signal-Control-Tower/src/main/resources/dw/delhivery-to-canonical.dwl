%dw 2.0
import try from dw::Runtime
output application/json

// Utility: Normalize carrier timestamp into UTC ISO-8601 string (yyyy-MM-dd'T'HH:mm:ss'Z')
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

var statusObj = payload.Status default {}
var rawStatus = upper(trim(statusObj.statusCode default statusObj.status default payload.status default "UNKNOWN"))

// Canonical status mapping dictionary matching Hackathon Use Case 08 specifications
var normalizedStatusMap = {
    "MANIFESTED": "LABEL_CREATED",
    "MF": "LABEL_CREATED",
    "SOFTDATA UPLOADED": "LABEL_CREATED",
    "PENDING": "PICKED_UP",
    "PP": "PICKED_UP",
    "PICKED UP": "PICKED_UP",
    "PICKED_UP": "PICKED_UP",
    "DISPATCHED": "IN_TRANSIT",
    "IN TRANSIT": "IN_TRANSIT",
    "IN_TRANSIT": "IN_TRANSIT",
    "IT": "IN_TRANSIT",
    "BAG IN": "ARRIVED_AT_HUB",
    "ARRIVED AT FACILITY": "ARRIVED_AT_HUB",
    "ARRIVED AT SORTING FACILITY": "ARRIVED_AT_HUB",
    "ARRIVED_AT_HUB": "ARRIVED_AT_HUB",
    "OUT FOR DELIVERY": "OUT_FOR_DELIVERY",
    "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
    "OFD": "OUT_FOR_DELIVERY",
    "VAN OUT": "OUT_FOR_DELIVERY",
    "UNDELIVERED": "DELIVERY_ATTEMPTED",
    "DELIVERY ATTEMPTED": "DELIVERY_ATTEMPTED",
    "DELIVERY_ATTEMPTED": "DELIVERY_ATTEMPTED",
    "UD": "DELIVERY_ATTEMPTED",
    "DELIVERED": "DELIVERED",
    "DL": "DELIVERED",
    "RTO": "RETURNED",
    "RETURN TO ORIGIN": "RETURNED",
    "RETURNED": "RETURNED",
    "RT": "RETURNED",
    "EXCEPTION": "EXCEPTION",
    "EX": "EXCEPTION",
    "DAMAGED": "EXCEPTION",
    "LOST": "EXCEPTION"
}

// Fallback to EXCEPTION for unrecognized status codes as required by N04
var canonicalStatus = normalizedStatusMap[rawStatus] default "EXCEPTION"

var rawScanTime = statusObj.statusDateTime default (
    if (payload.Scans != null and sizeOf(payload.Scans) > 0) payload.Scans[0].scanDateTime 
    else (now() as String {format: "yyyy-MM-dd'T'HH:mm:ssXXX"})
)
var eventTimeUtc = toUtcIsoString(rawScanTime) default ((now() >> "UTC") as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"})

var rawEta = payload.ExpectedDeliveryDate default payload.eta default null
var etaUtc = toUtcIsoString(rawEta)

var trackingNum = trim(payload.waybill default payload.waybill_no default payload.tracking_number default payload.awb default "UNKNOWN_WAYBILL")
var compactTs = eventTimeUtc replace /[-:TZ]/ with ""
var eventKeyCalc = "DELHIVERY-" ++ trackingNum ++ "-" ++ (rawStatus replace " " with "_") ++ "-" ++ compactTs
var scanLocation = if (payload.Scans != null and sizeOf(payload.Scans) > 0) payload.Scans[0].scannedLocation default "N/A" else "N/A"
---
{
    eventId: payload.eventId default ("EVT-DEL-" ++ compactTs),
    eventKey: payload.eventKey default eventKeyCalc,
    shipmentId: vars.targetShipmentId default null,
    trackingNumber: trackingNum,
    carrier: "DELHIVERY",
    carrierEventCode: rawStatus,
    originalStatus: rawStatus,
    normalizedStatus: canonicalStatus,
    eventTimestamp: eventTimeUtc,
    receivedTimestamp: (now() >> "UTC") as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"},
    location: scanLocation,
    description: statusObj.instructions default statusObj.status default ("Delhivery scan: " ++ rawStatus),
    estimatedDeliveryTime: etaUtc,
    promisedDeliveryTime: vars.promisedDeliveryTime default null,
    correlationId: vars.correlationId default uuid(),
    isDuplicate: false,
    isOutOfOrder: false,
    isPendingUnknown: false,
    sourcePayload: write(payload, "application/json")
}
