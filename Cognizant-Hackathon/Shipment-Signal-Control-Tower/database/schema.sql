-- ==============================================================================
-- Cognizant MuleSoft Hackathon 2026-2027
-- Use Case 08: Logistics - Real-Time Multi-Carrier Shipment Tracking
-- Control Tower Relational Database Schema (MySQL 8.0)
-- Database Name: shipment_control_tower
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS shipment_control_tower
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE shipment_control_tower;

-- Drop tables in reverse foreign key dependency order for clean recreation
DROP TABLE IF EXISTS integration_alerts;
DROP TABLE IF EXISTS notification_outbox;
DROP TABLE IF EXISTS pending_tracking_events;
DROP TABLE IF EXISTS shipment_tracking_events;
DROP TABLE IF EXISTS shipments;

-- ------------------------------------------------------------------------------
-- Table 1: shipments
-- Purpose: Master state record for all registered packages in the control tower.
--          Stores the latest forward-progressed status, current risk level, and SLA timestamps.
-- ------------------------------------------------------------------------------
CREATE TABLE shipments (
    shipment_id VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(50) NOT NULL,
    carrier VARCHAR(30) NOT NULL,
    origin_location VARCHAR(120) DEFAULT NULL,
    destination_location VARCHAR(120) DEFAULT NULL,
    current_status VARCHAR(50) NOT NULL DEFAULT 'LABEL_CREATED',
    status_rank INT NOT NULL DEFAULT 10,
    last_event_timestamp DATETIME(3) DEFAULT NULL,
    estimated_delivery_time DATETIME(3) DEFAULT NULL,
    promised_delivery_time DATETIME(3) DEFAULT NULL,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    risk_reason VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (shipment_id),
    UNIQUE KEY uq_shipments_tracking_number (tracking_number),
    INDEX idx_shipments_carrier (carrier),
    INDEX idx_shipments_status (current_status),
    INDEX idx_shipments_risk (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table 2: shipment_tracking_events
-- Purpose: Immutable audit trail of every received tracking scan.
--          Enforces duplicate prevention via unique event_key, and stores both
--          original carrier status codes and normalized canonical statuses.
-- ------------------------------------------------------------------------------
CREATE TABLE shipment_tracking_events (
    id BIGINT AUTO_INCREMENT NOT NULL,
    event_key VARCHAR(150) NOT NULL,
    event_id VARCHAR(100) DEFAULT NULL,
    shipment_id VARCHAR(50) DEFAULT NULL,
    tracking_number VARCHAR(50) NOT NULL,
    carrier VARCHAR(30) NOT NULL,
    original_status VARCHAR(50) NOT NULL,
    normalized_status VARCHAR(50) NOT NULL,
    event_timestamp DATETIME(3) NOT NULL,
    received_timestamp DATETIME(3) NOT NULL,
    location VARCHAR(150) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    processing_result VARCHAR(50) NOT NULL, -- PROCESSED, DUPLICATE_SUPPRESSED, OUT_OF_ORDER_RECORDED, REPLAYED
    correlation_id VARCHAR(64) DEFAULT NULL,
    source_payload LONGTEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_events_key (event_key),
    INDEX idx_events_shipment_id (shipment_id),
    INDEX idx_events_tracking_number (tracking_number),
    INDEX idx_events_carrier (carrier),
    INDEX idx_events_timestamp (event_timestamp),
    CONSTRAINT fk_events_shipment FOREIGN KEY (shipment_id) 
        REFERENCES shipments (shipment_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table 3: pending_tracking_events
-- Purpose: Quarantine buffer for scans arriving for tracking numbers not yet registered
--          in the master shipments table. Allows safe reconciliation when registered.
-- ------------------------------------------------------------------------------
CREATE TABLE pending_tracking_events (
    id BIGINT AUTO_INCREMENT NOT NULL,
    event_key VARCHAR(150) NOT NULL,
    tracking_number VARCHAR(50) NOT NULL,
    carrier VARCHAR(30) NOT NULL,
    payload LONGTEXT NOT NULL,
    received_timestamp DATETIME(3) NOT NULL,
    retry_count INT NOT NULL DEFAULT 0,
    processing_status VARCHAR(30) NOT NULL DEFAULT 'PENDING', -- PENDING, RECONCILED, FAILED
    last_error VARCHAR(255) DEFAULT NULL,
    correlation_id VARCHAR(64) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_pending_event_key (event_key),
    INDEX idx_pending_tracking_number (tracking_number),
    INDEX idx_pending_status (processing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table 4: notification_outbox
-- Purpose: Transactional outbox for customer milestone notifications.
--          Guarantees at-least-once notification delivery even if the message queue
--          or downstream communication gateway experiences transient downtime.
-- ------------------------------------------------------------------------------
CREATE TABLE notification_outbox (
    id BIGINT AUTO_INCREMENT NOT NULL,
    notification_id VARCHAR(64) NOT NULL,
    shipment_id VARCHAR(50) DEFAULT NULL,
    tracking_number VARCHAR(50) NOT NULL,
    carrier VARCHAR(30) NOT NULL,
    milestone VARCHAR(50) NOT NULL,
    message_body TEXT NOT NULL,
    channels VARCHAR(100) NOT NULL DEFAULT 'SMS,EMAIL',
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING', -- PENDING, QUEUED, SENT, FAILED
    retry_count INT NOT NULL DEFAULT 0,
    last_error VARCHAR(255) DEFAULT NULL,
    correlation_id VARCHAR(64) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME(3) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_outbox_notif_id (notification_id),
    INDEX idx_outbox_tracking (tracking_number),
    INDEX idx_outbox_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table 5: integration_alerts
-- Purpose: Operational telemetry table storing exception signals, SLA breaches,
--          DLQ routing events, and authentication failures for tower operators.
-- ------------------------------------------------------------------------------
CREATE TABLE integration_alerts (
    id BIGINT AUTO_INCREMENT NOT NULL,
    alert_id VARCHAR(64) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- SLA_BREACH, DLQ_EVENT, AUTH_FAILURE, DB_ERROR, UNKNOWN_STATUS
    severity VARCHAR(20) NOT NULL DEFAULT 'WARNING', -- INFO, WARNING, HIGH, CRITICAL
    tracking_number VARCHAR(50) DEFAULT NULL,
    carrier VARCHAR(30) DEFAULT NULL,
    alert_message TEXT NOT NULL,
    correlation_id VARCHAR(64) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_alert_id (alert_id),
    INDEX idx_alerts_type (alert_type),
    INDEX idx_alerts_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
