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

// Extract raw carrier status code or text
var rawStatus = upper(trim(payload.status_code default payload.status default "UNKNOWN"))

// Canonical status mapping dictionary matching Hackathon Use Case 08 specifications
var normalizedStatusMap = {
    "LC": "LABEL_CREATED",
    "BK": "LABEL_CREATED",
    "PU": "PICKED_UP",
    "IT": "IN_TRANSIT",
    "DP": "IN_TRANSIT",
    "AR": "ARRIVED_AT_HUB",
    "HUB": "ARRIVED_AT_HUB",
    "OFD": "OUT_FOR_DELIVERY",
    "OD": "OUT_FOR_DELIVERY",
    "UD": "DELIVERY_ATTEMPTED",
    "NA": "DELIVERY_ATTEMPTED",
    "DL": "DELIVERED",
    "OK": "DELIVERED",
    "RT": "RETURNED",
    "RTO": "RETURNED",
    "RDL": "RETURNED",
    "EX": "EXCEPTION",
    "HLD": "EXCEPTION",
    "DMG": "EXCEPTION"
}

// Fallback to EXCEPTION for unrecognized status codes as required by N04
var canonicalStatus = normalizedStatusMap[rawStatus] default "EXCEPTION"

// Standardize timestamps
var rawScanTime = payload.scan_date_time default payload.scan_datetime default (now() as String {format: "yyyy-MM-dd'T'HH:mm:ssXXX"})
var eventTimeUtc = toUtcIsoString(rawScanTime) default ((now() >> "UTC") as String {format: "yyyy-MM-dd'T'HH:mm:ss'Z'"})

var rawEta = payload.eta default null
var etaUtc = toUtcIsoString(rawEta)

var trackingNum = trim(payload.awb_no default payload.awb default payload.tracking_number default "UNKNOWN_AWB")
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
    location: trim((payload.location_name default payload.scan_location default "") ++ " (" ++ (payload.location_code default "N/A") ++ ")"),
    description: payload.status_description default ("BlueDart status scan: " ++ rawStatus),
    estimatedDeliveryTime: etaUtc,
    promisedDeliveryTime: vars.promisedDeliveryTime default null,
    correlationId: vars.correlationId default uuid(),
    isDuplicate: false,
    isOutOfOrder: false,
    isPendingUnknown: false,
    sourcePayload: write(payload, "application/json")
}
