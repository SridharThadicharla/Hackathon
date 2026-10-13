-- ==============================================================================
-- Cognizant MuleSoft Hackathon 2026-2027
-- Use Case 08: Logistics - Real-Time Multi-Carrier Shipment Tracking
-- Control Tower Sample / Seed Master Data
-- Database Name: shipment_control_tower
-- ==============================================================================

USE shipment_control_tower;

-- Clear previous sample records
DELETE FROM integration_alerts;
DELETE FROM notification_outbox;
DELETE FROM pending_tracking_events;
DELETE FROM shipment_tracking_events;
DELETE FROM shipments;

-- ------------------------------------------------------------------------------
-- Seed Master Shipments
-- ------------------------------------------------------------------------------

-- Shipment 1: BlueDart Express - Standard Flow (Mumbai FC to Delhi DC)
INSERT INTO shipments (
    shipment_id, tracking_number, carrier, origin_location, destination_location,
    current_status, status_rank, last_event_timestamp, estimated_delivery_time,
    promised_delivery_time, risk_level, risk_reason
) VALUES (
    'SHP-1001', 'BD-987654321', 'BLUEDART', 'Mumbai Fulfillment Center', 'Delhi Regional Hub',
    'LABEL_CREATED', 10, '2026-10-10 09:00:00', '2026-10-14 18:00:00',
    '2026-10-15 18:00:00', 'ON_TRACK', 'Shipment manifested. Awaiting carrier pickup.'
);

-- Shipment 2: Delhivery Logistics - In-Transit Flow (Bengaluru to Hyderabad)
INSERT INTO shipments (
    shipment_id, tracking_number, carrier, origin_location, destination_location,
    current_status, status_rank, last_event_timestamp, estimated_delivery_time,
    promised_delivery_time, risk_level, risk_reason
) VALUES (
    'SHP-1002', 'DELH-11223344', 'DELHIVERY', 'Bengaluru Sorting Center', 'Hyderabad DC',
    'PICKED_UP', 20, '2026-10-10 10:30:00', '2026-10-13 14:00:00',
    '2026-10-14 20:00:00', 'ON_TRACK', 'Package picked up by Delhivery agent.'
);

-- Shipment 3: BlueDart Express - Critical Breach Test (Chennai to Kolkata)
-- Promised SLA was earlier than current time to trigger DELAYED / CRITICAL risk calculation
INSERT INTO shipments (
    shipment_id, tracking_number, carrier, origin_location, destination_location,
    current_status, status_rank, last_event_timestamp, estimated_delivery_time,
    promised_delivery_time, risk_level, risk_reason
) VALUES (
    'SHP-1003', 'BD-123456789', 'BLUEDART', 'Chennai Central Warehouse', 'Kolkata East Hub',
    'IN_TRANSIT', 30, '2026-10-09 14:00:00', '2026-10-14 18:00:00',
    '2026-10-10 12:00:00', 'DELAYED', 'Promised delivery SLA expired while package is still in transit.'
);

-- Shipment 4: Delhivery Logistics - Out for Delivery Scenario (Pune to Ahmedabad)
INSERT INTO shipments (
    shipment_id, tracking_number, carrier, origin_location, destination_location,
    current_status, status_rank, last_event_timestamp, estimated_delivery_time,
    promised_delivery_time, risk_level, risk_reason
) VALUES (
    'SHP-1004', 'DELH-55667788', 'DELHIVERY', 'Pune West Depot', 'Ahmedabad Sorting Facility',
    'ARRIVED_AT_HUB', 35, '2026-10-10 11:15:00', '2026-10-12 16:00:00',
    '2026-10-13 18:00:00', 'ON_TRACK', 'Package processed at Ahmedabad regional hub.'
);

-- Shipment 5: Reconciliation Demonstration Target (Registered after initial scan quarantine)
INSERT INTO shipments (
    shipment_id, tracking_number, carrier, origin_location, destination_location,
    current_status, status_rank, last_event_timestamp, estimated_delivery_time,
    promised_delivery_time, risk_level, risk_reason
) VALUES (
    'SHP-1005', 'DELH-99887766', 'DELHIVERY', 'Gurugram Warehousing Park', 'Jaipur City Hub',
    'LABEL_CREATED', 10, '2026-10-10 08:00:00', '2026-10-13 18:00:00',
    '2026-10-14 12:00:00', 'ON_TRACK', 'Shipment order generated in WMS.'
);

-- ------------------------------------------------------------------------------
-- Seed Sample Notification Outbox Messages (Customer Alerts)
-- ------------------------------------------------------------------------------
INSERT INTO notification_outbox (
    notification_id, shipment_id, tracking_number, carrier, milestone,
    message_body, channels, status, correlation_id, created_at, sent_at
) VALUES (
    'NOTIF-SEED-1001', 'SHP-1001', 'BD-987654321', 'BLUEDART', 'DELIVERED',
    'Delivered successfully! Your shipment has been delivered at destination.',
    'EMAIL,SMS', 'SENT', 'c85d8984-9df2-43bb-a53f-a3cf6ad35501',
    '2026-10-11 16:30:00', '2026-10-11 16:30:01'
),
(
    'NOTIF-SEED-1002', 'SHP-1002', 'DELH-11223344', 'DELHIVERY', 'OUT_FOR_DELIVERY',
    'Out for delivery! Your package is with our delivery agent and will arrive today.',
    'EMAIL,SMS', 'SENT', 'ed70661a-e2aa-4ffa-ae15-e90d70343b0a',
    '2026-10-11 08:30:00', '2026-10-11 08:30:02'
);

