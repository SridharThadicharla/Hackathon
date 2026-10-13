# 08 – MySQL Database Setup & Management Guide

**Project**: Shipment Signal Control Tower  
**RDBMS**: MySQL Server 8.0 Community Edition  
**Database Name**: `shipment_control_tower`  
**Schema File**: `database/schema.sql`  
**Sample Data File**: `database/sample-data.sql`  
**Verification File**: `database/verification-queries.sql`  

---

## 1. Prerequisites

Before starting the MuleSoft application, your MySQL 8.0 database must be active and accessible:
- **MySQL Version**: MySQL 8.0.x (verified on MySQL 8.0.30+).
- **Service Status**: Ensure the Windows service `MySQL80` is running.
- **Verification Command** (Run in PowerShell):
  ```powershell
  Get-Service -Name "MySQL80"
  ```
- **Start Service if Stopped**:
  ```powershell
  Start-Service -Name "MySQL80"
  ```

---

## 2. Database Creation & Execution Instructions

### 2.1 Using MySQL Command Line Client
Execute the schema script using the following command in PowerShell:

```powershell
# 1. Execute Schema DDL (Creates database and all 5 tables)
Get-Content -Path "database\schema.sql" -Raw | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -proot

# 2. Seed Master Sample Shipments
Get-Content -Path "database\sample-data.sql" -Raw | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -proot
```

### 2.2 Using MySQL Workbench
1. Open **MySQL Workbench 8.0 CE**.
2. Click on your local MySQL connection (e.g. `Local instance MySQL80` on `localhost:3306`).
3. Click **File -> Open SQL Script...** and select `database/schema.sql`.
4. Click the yellow lightning bolt icon (**Execute**) to run the entire script.
5. Repeat for `database/sample-data.sql`.
6. In the left **Schemas** pane, click Refresh. You will see `shipment_control_tower` with all 5 tables!

---

## 3. Comprehensive Schema Architecture (All 5 Tables)

### Table 1: `shipments` (Master State)
Stores the current state, latest forward-progressed status, and SLA risk level for every manifested package.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `shipment_id` | `VARCHAR(50)` | `PRIMARY KEY` | Unique internal shipment ID (e.g. `SHP-1001`) |
| `tracking_number` | `VARCHAR(50)` | `UNIQUE KEY`, `NOT NULL` | Courier AWB / Waybill number (e.g. `BD-987654321`) |
| `carrier` | `VARCHAR(30)` | `INDEX`, `NOT NULL` | Courier partner (`BLUEDART`, `DELHIVERY`) |
| `origin_location` | `VARCHAR(120)` | `NULL` | Origin fulfillment warehouse / city |
| `destination_location` | `VARCHAR(120)` | `NULL` | Destination customer city / regional hub |
| `current_status` | `VARCHAR(50)` | `INDEX`, `NOT NULL` | Latest canonical status (e.g. `IN_TRANSIT`) |
| `status_rank` | `INT` | `NOT NULL DEFAULT 10` | Monotonically increasing progression rank |
| `last_event_timestamp`| `DATETIME(3)` | `NULL` | Timestamp of latest applied scan |
| `estimated_delivery_time`| `DATETIME(3)` | `NULL` | Carrier revised delivery estimate (ETA) |
| `promised_delivery_time` | `DATETIME(3)` | `NULL` | Customer SLA delivery commitment date |
| `risk_level` | `VARCHAR(20)` | `INDEX`, `NOT NULL` | Computed SLA risk (`ON_TRACK`, `AT_RISK`, `DELAYED`, `CRITICAL`) |
| `risk_reason` | `VARCHAR(255)` | `NULL` | Human-readable explanation of risk score |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Initial record manifestation timestamp |
| `updated_at` | `TIMESTAMP` | `AUTO UPDATE` | Last database update timestamp |

---

### Table 2: `shipment_tracking_events` (Immutable Audit History)
Stores every physical scan received from couriers. Guarantees deduplication via unique key and provides full traceability.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT AUTO_INCREMENT` | `PRIMARY KEY` | Auto-generated surrogate event ID |
| `event_key` | `VARCHAR(150)` | `UNIQUE KEY`, `NOT NULL`| Composite idempotency key (`CARRIER-AWB-STATUS-TS`) |
| `event_id` | `VARCHAR(100)` | `NULL` | Courier external scan event ID |
| `shipment_id` | `VARCHAR(50)` | `FOREIGN KEY`, `INDEX` | References `shipments(shipment_id)` |
| `tracking_number` | `VARCHAR(50)` | `INDEX`, `NOT NULL` | Associated AWB / Waybill |
| `carrier` | `VARCHAR(30)` | `INDEX`, `NOT NULL` | Courier partner |
| `original_status` | `VARCHAR(50)` | `NOT NULL` | Raw carrier status code (e.g. `UD`, `OFD`, `IT`) |
| `normalized_status`| `VARCHAR(50)` | `NOT NULL` | Canonical status (e.g. `DELIVERY_ATTEMPTED`) |
| `event_timestamp` | `DATETIME(3)` | `INDEX`, `NOT NULL` | When scan occurred at courier facility |
| `received_timestamp`| `DATETIME(3)` | `NOT NULL` | When control tower ingested the webhook |
| `location` | `VARCHAR(150)` | `NULL` | Scan facility code and name |
| `description` | `TEXT` | `NULL` | Courier scan notes or instructions |
| `processing_result`| `VARCHAR(50)` | `NOT NULL` | `PROCESSED`, `DUPLICATE_SUPPRESSED`, `OUT_OF_ORDER_RECORDED` |
| `correlation_id` | `VARCHAR(64)` | `NULL` | Distributed tracing ID |
| `source_payload` | `LONGTEXT` | `NULL` | Raw JSON payload received from carrier |

---

### Table 3: `pending_tracking_events` (Quarantine Buffer)
Holds scans arriving for packages not yet manifested in the `shipments` master table, preventing data loss.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT AUTO_INCREMENT` | `PRIMARY KEY` | Quarantine row ID |
| `event_key` | `VARCHAR(150)` | `UNIQUE KEY`, `NOT NULL`| Unique idempotency event key |
| `tracking_number` | `VARCHAR(50)` | `INDEX`, `NOT NULL` | Unrecognized tracking number |
| `carrier` | `VARCHAR(30)` | `NOT NULL` | Courier partner |
| `payload` | `LONGTEXT` | `NOT NULL` | Preserved raw JSON payload |
| `received_timestamp`| `DATETIME(3)` | `NOT NULL` | Webhook ingestion timestamp |
| `retry_count` | `INT` | `NOT NULL DEFAULT 0` | Times re-scanned or retry attempted |
| `processing_status`| `VARCHAR(30)` | `INDEX`, `NOT NULL` | `PENDING`, `RECONCILED`, `FAILED` |
| `last_error` | `VARCHAR(255)` | `NULL` | Explanation (e.g. unmanifested shipment) |
| `correlation_id` | `VARCHAR(64)` | `NULL` | Distributed tracing ID |

---

### Table 4: `notification_outbox` (Transactional Outbox)
Guarantees reliable at-least-once customer notification delivery even during queue or SMS gateway outages.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT AUTO_INCREMENT` | `PRIMARY KEY` | Outbox record ID |
| `notification_id` | `VARCHAR(64)` | `UNIQUE KEY`, `NOT NULL`| Unique alert ID (e.g. `NOTIF-3a8f1b2c`) |
| `shipment_id` | `VARCHAR(50)` | `NULL` | Internal shipment identifier |
| `tracking_number` | `VARCHAR(50)` | `INDEX`, `NOT NULL` | Associated tracking number |
| `carrier` | `VARCHAR(30)` | `NOT NULL` | Courier partner |
| `milestone` | `VARCHAR(50)` | `NOT NULL` | Trigger milestone (`OUT_FOR_DELIVERY`, etc.) |
| `message_body` | `TEXT` | `NOT NULL` | Rendered customer notification text |
| `channels` | `VARCHAR(100)` | `NOT NULL` | Target channels (e.g. `SMS,EMAIL`) |
| `status` | `VARCHAR(30)` | `INDEX`, `NOT NULL` | `PENDING`, `QUEUED`, `SENT`, `FAILED` |
| `retry_count` | `INT` | `NOT NULL DEFAULT 0` | Retry attempts |
| `correlation_id` | `VARCHAR(64)` | `NULL` | Tracing ID |
| `sent_at` | `DATETIME(3)` | `NULL` | Dispatch confirmation timestamp |

---

### Table 5: `integration_alerts` (Operational Telemetry)
Stores SLA breaches, DLQ routing events, authentication failures, and integration warnings for tower operators.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT AUTO_INCREMENT` | `PRIMARY KEY` | Alert row ID |
| `alert_id` | `VARCHAR(64)` | `UNIQUE KEY`, `NOT NULL`| Unique alert identifier (e.g. `ALT-7e2a9c14`) |
| `alert_type` | `VARCHAR(50)` | `INDEX`, `NOT NULL` | `SLA_BREACH`, `DLQ_EVENT`, `AUTH_FAILURE`, `DB_ERROR` |
| `severity` | `VARCHAR(20)` | `INDEX`, `NOT NULL` | `INFO`, `WARNING`, `HIGH`, `CRITICAL` |
| `tracking_number` | `VARCHAR(50)` | `NULL` | Associated package if applicable |
| `carrier` | `VARCHAR(30)` | `NULL` | Associated carrier partner |
| `alert_message` | `TEXT` | `NOT NULL` | Operational telemetry diagnostic message |
| `correlation_id` | `VARCHAR(64)` | `NULL` | Distributed tracing ID |

---

## 4. MuleSoft Database Configuration & Connection Properties

Configured in `src/main/mule/global-config.xml`:

```xml
<db:config name="Database_Config" doc:name="Database Config">
    <db:my-sql-connection 
        host="${db.host}" 
        port="${db.port}" 
        user="${db.user}" 
        password="${db.password}" 
        database="${db.database}">
        <db:connection-properties>
            <db:connection-property key="serverTimezone" value="UTC" />
            <db:connection-property key="useSSL" value="false" />
            <db:connection-property key="allowPublicKeyRetrieval" value="true" />
            <db:connection-property key="autoReconnect" value="true" />
        </db:connection-properties>
    </db:my-sql-connection>
</db:config>
```

Values are injected from `src/main/resources/config/mule-dev.yaml`:
```yaml
db:
  host: "localhost"
  port: "3306"
  user: "root"
  password: "root"
  database: "shipment_control_tower"
  connectionTimeout: "30000"
```

---

## 5. Seed Data & Test Tracking Numbers

| Tracking Number | Carrier | Shipment ID | Initial Status | Promised SLA | Test Purpose in Postman |
|---|---|---|---|---|---|
| `BD-987654321` | BlueDart | `SHP-1001` | `LABEL_CREATED` | `2026-10-15 18:00:00` | In-transit scan, duplicate test, out-of-order test |
| `DELH-11223344` | Delhivery | `SHP-1002` | `PICKED_UP` | `2026-10-14 20:00:00` | Out for delivery scan, milestone notification test |
| `BD-123456789` | BlueDart | `SHP-1003` | `IN_TRANSIT` | `2026-10-10 12:00:00` | Expired SLA test -> triggers `DELAYED` risk score |
| `DELH-55667788` | Delhivery | `SHP-1004` | `ARRIVED_AT_HUB` | `2026-10-13 18:00:00` | Regional sorting hub arrival test |
| `DELH-99887766` | Delhivery | `SHP-1005` | Unmanifested | `2026-10-14 12:00:00` | Quarantine buffer test & batch reconciliation |

---

## 6. Verification Queries

Run these queries in MySQL Workbench or CLI to verify system behavior:

```sql
USE shipment_control_tower;

-- 1. Check current status and risk level of all shipments
SELECT shipment_id, tracking_number, carrier, current_status, status_rank, risk_level, risk_reason FROM shipments;

-- 2. Check full chronological audit trail
SELECT id, event_key, tracking_number, normalized_status, event_timestamp, processing_result FROM shipment_tracking_events ORDER BY id DESC;

-- 3. Verify zero unhandled duplicates
SELECT event_key, COUNT(*) FROM shipment_tracking_events GROUP BY event_key HAVING COUNT(*) > 1;

-- 4. Check quarantined scans
SELECT id, event_key, tracking_number, processing_status, last_error FROM pending_tracking_events;

-- 5. Check notification outbox
SELECT notification_id, tracking_number, milestone, status, sent_at FROM notification_outbox;
```

---

## 7. Database Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `Access denied for user 'root'@'localhost'` | Incorrect password in `mule-dev.yaml` | Update `db.password` in `config/mule-dev.yaml` to match MySQL root password. |
| `Unknown database 'shipment_control_tower'` | Schema script not executed | Run `schema.sql` via MySQL CLI or Workbench. |
| `Communications link failure / Connection refused` | MySQL service stopped | Start MySQL service via `Start-Service MySQL80`. |
| `Public Key Retrieval is not allowed` | MySQL 8.0 caching sha2 authentication | Handled automatically by `allowPublicKeyRetrieval=true` in `Database_Config`. |
| `The server time zone value is unrecognized` | TimeZone disparity | Handled automatically by `serverTimezone=UTC` in `Database_Config`. |
