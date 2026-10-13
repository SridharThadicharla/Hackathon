-- ==============================================================================
-- Cognizant MuleSoft Hackathon 2026-2027
-- Use Case 08: Logistics - Real-Time Multi-Carrier Shipment Tracking
-- Database Verification Queries (MySQL 8.0)
-- ==============================================================================

USE shipment_control_tower;

-- 1. Check Master Shipment State & Risk Status
SELECT 
    shipment_id,
    tracking_number,
    carrier,
    current_status,
    status_rank,
    last_event_timestamp,
    estimated_delivery_time,
    promised_delivery_time,
    risk_level,
    risk_reason,
    updated_at
FROM shipments
ORDER BY shipment_id ASC;

-- 2. Check Chronological Event History & Audit Trail
SELECT 
    id,
    event_key,
    event_id,
    shipment_id,
    tracking_number,
    carrier,
    original_status,
    normalized_status,
    event_timestamp,
    received_timestamp,
    processing_result,
    correlation_id
FROM shipment_tracking_events
ORDER BY event_timestamp DESC, id DESC;

-- 3. Verify Duplicate Event Prevention (Idempotency)
-- Check duplicate event keys or events suppressed as DUPLICATE_SUPPRESSED
SELECT 
    event_key,
    COUNT(*) AS occurrence_count,
    MAX(processing_result) AS last_result
FROM shipment_tracking_events
GROUP BY event_key
HAVING COUNT(*) > 1;

-- 4. Check Quarantined Events for Unknown Shipments
SELECT 
    id,
    event_key,
    tracking_number,
    carrier,
    received_timestamp,
    retry_count,
    processing_status,
    last_error,
    correlation_id
FROM pending_tracking_events
ORDER BY received_timestamp DESC;

-- 5. Check Customer Milestone Notification Outbox
SELECT 
    id,
    notification_id,
    tracking_number,
    carrier,
    milestone,
    status,
    channels,
    message_body,
    created_at,
    sent_at
FROM notification_outbox
ORDER BY created_at DESC;

-- 6. Check Operational Telemetry & Integration Alerts
SELECT 
    id,
    alert_id,
    alert_type,
    severity,
    tracking_number,
    carrier,
    alert_message,
    created_at
FROM integration_alerts
ORDER BY created_at DESC;

-- 7. Carrier Pulse Aggregated Metrics
SELECT 
    c.carrier,
    COALESCE(e.total_events, 0) AS total_events_received,
    COALESCE(e.processed_events, 0) AS successfully_processed,
    COALESCE(e.duplicate_events, 0) AS duplicate_events_suppressed,
    COALESCE(e.out_of_order_events, 0) AS out_of_order_events,
    COALESCE(p.pending_events, 0) AS pending_unknown_quarantined,
    COALESCE(s.active_shipments, 0) AS active_shipments
FROM (
    SELECT 'BLUEDART' AS carrier UNION ALL SELECT 'DELHIVERY' AS carrier
) c
LEFT JOIN (
    SELECT carrier,
           COUNT(*) AS total_events,
           SUM(CASE WHEN processing_result IN ('PROCESSED', 'REPLAYED') THEN 1 ELSE 0 END) AS processed_events,
           SUM(CASE WHEN processing_result = 'DUPLICATE_SUPPRESSED' THEN 1 ELSE 0 END) AS duplicate_events,
           SUM(CASE WHEN processing_result = 'OUT_OF_ORDER_RECORDED' THEN 1 ELSE 0 END) AS out_of_order_events
    FROM shipment_tracking_events
    GROUP BY carrier
) e ON c.carrier = e.carrier
LEFT JOIN (
    SELECT carrier, COUNT(*) AS pending_events
    FROM pending_tracking_events
    WHERE processing_status = 'PENDING'
    GROUP BY carrier
) p ON c.carrier = p.carrier
LEFT JOIN (
    SELECT carrier, COUNT(*) AS active_shipments
    FROM shipments
    WHERE current_status NOT IN ('DELIVERED', 'RETURNED')
    GROUP BY carrier
) s ON c.carrier = s.carrier;
