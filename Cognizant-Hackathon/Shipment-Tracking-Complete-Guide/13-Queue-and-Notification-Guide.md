# 13 – Queue & Notification Architecture Guide

**Project**: Shipment Signal Control Tower  
**Messaging Technologies**: MuleSoft Anypoint VM Connector (Local Reliable Persistent Queues) / Anypoint MQ (CloudHub)  
**Configuration File**: `src/main/mule/notification-queue.xml`  
**Transactional Table**: `notification_outbox`  

---

## 1. Why Messaging Queues Are Essential in Logistics

Carrier webhooks require immediate HTTP acknowledgments (usually `< 200ms`). If a Mule application attempts to invoke external SMS gateways (e.g. Twilio, Gupshup) or SendGrid Email APIs synchronously inside the inbound webhook flow:
- Any latency or timeout in the SMS gateway causes the webhook to hang or fail.
- Carrier webhooks timeout and trigger aggressive retry cascades.
- Inbound thread starvation degrades overall tracking throughput.

**The Solution**: Asynchronous decoupling via persistent message queues combined with the **Transactional Notification Outbox Pattern**.

```text
[Webhook Inbound Flow]
         │
         ▼
[Milestone Filter: PICKED_UP, OFD, DELIVERED, EXCEPTION, ATTEMPTED]
         │
         ▼
[Step 1: Write to notification_outbox table (status: 'QUEUED')] ──► (Guaranteed Durability)
         │
         ▼
[Step 2: Publish to VM Queue (shipment-milestone-queue)]
         │
         ▼
[HTTP 200 ACK Returned to Carrier Immediately (< 50ms)]

───────────────────────────────────────────────────────────────────────────
(Asynchronous Processing in Background)

[VM Queue Listener Consumer]
         │
         ▼
[Dispatch Alert via Multi-Channel Gateway (SMS, Email, Push)]
         │
         ▼
[Step 3: Update notification_outbox table (status: 'SENT', sent_at: NOW())]
```

---

## 2. Customer Milestone Notification Filtering

Not every tracking scan should trigger a customer notification. Over-notifying customers about internal linehaul hops causes notification fatigue and escalates SMS gateway costs.

### 2.1 The Eligibility Filter Rule
In `src/main/mule/notification-queue.xml`, notifications are dispatched **ONLY IF**:
1. Canonical status is a customer milestone:
   `['PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED', 'EXCEPTION', 'DELIVERY_ATTEMPTED'] contains vars.canonicalEvent.normalizedStatus`
2. **AND** the event is not a duplicate: `vars.isDuplicate == false`
3. **AND** the event is not out-of-order: `vars.isOutOfOrder == false`
4. **AND** the event is not an unmanifested scan: `vars.isPendingUnknown == false`

### 2.2 Suppressed Scans
- `LABEL_CREATED`: Internal manifestation; package has not physically moved.
- `IN_TRANSIT`: Internal linehaul scans between airports and freight terminals.
- `ARRIVED_AT_HUB`: Internal sorting facility scans.
- Duplicate and stale scans: Always suppressed.

---

## 3. Transactional Outbox Pattern Implementation

The **Transactional Outbox Pattern** ensures that a notification is never lost, even if the Mule application crashes before publishing to the queue, or if the queue is temporarily down:

### 3.1 Outbox Schema (`notification_outbox`)
```sql
CREATE TABLE notification_outbox (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notification_id VARCHAR(64) NOT NULL UNIQUE,
    shipment_id VARCHAR(50) DEFAULT NULL,
    tracking_number VARCHAR(50) NOT NULL,
    carrier VARCHAR(30) NOT NULL,
    milestone VARCHAR(50) NOT NULL,
    message_body TEXT NOT NULL,
    channels VARCHAR(100) NOT NULL DEFAULT 'SMS,EMAIL',
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING', -- PENDING, QUEUED, SENT, FAILED
    retry_count INT NOT NULL DEFAULT 0,
    correlation_id VARCHAR(64) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME(3) DEFAULT NULL
);
```

### 3.2 Notification Lifecycle Statuses
1. **`QUEUED`**: Record inserted into `notification_outbox` and published to `shipment-milestone-queue`.
2. **`SENT`**: Asynchronous consumer successfully dispatches alert and records `sent_at` timestamp.
3. **`FAILED`**: Dispatch encountered unrecoverable downstream communication error.

---

## 4. Anypoint VM Connector Configuration (`global-config.xml`)

Local environments utilize the **MuleSoft VM Connector**, providing disk-persisted, transactional FIFO queues:

```xml
<vm:config name="VM_Config" doc:name="VM Config">
    <vm:queues>
        <!-- Primary FIFO Milestone Notification Queue -->
        <vm:queue queueName="${queue.milestoneQueue}" queueType="PERSISTENT" />
        <!-- Dead-Letter Queue for Poison Messages -->
        <vm:queue queueName="${queue.deadLetterQueue}" queueType="PERSISTENT" />
    </vm:queues>
</vm:config>
```

Configured in `config/mule-dev.yaml`:
```yaml
queue:
  provider: "vm"
  milestoneQueue: "shipment-milestone-queue"
  deadLetterQueue: "shipment-milestone-dlq"
```

---

## 5. Email Notification Integration (100% Free & Hackathon-Ready)

### 5.1 Why Email is the Best Notification Channel for Hackathons
1. **100% Free**: Unlike SMS gateways (Twilio, Gupshup, AWS SNS) which demand paid plans, credit card verification, or phone number whitelistings, Email can be tested with zero financial cost.
2. **Rich HTML Templating**: Allows embedding tracking tables, carrier badges, ETA timestamps, and delay risk alerts.
3. **Enterprise Resilience**: Employs the **Asynchronous Transactional Outbox Pattern** so carrier webhooks respond in under 50ms without waiting for third-party email servers.

### 5.2 Email Notification Flow in `src/main/mule/notification-queue.xml`
```text
[Webhook Inbound Flow]
       │  (Milestone Status: e.g., DELIVERED, OUT_FOR_DELIVERY)
       ▼
[subflow-publish-milestone-notification]
       │  • Builds Notification JSON & extracts customer email
       │  • Inserts record into MySQL `notification_outbox` (Status: 'QUEUED')
       ▼
[Publish to VM Queue: `shipment-milestone-queue`]
       │
       ▼ (Returns HTTP 200 OK immediately to BlueDart / Delhivery)
────────────────────────────────────────────────────────────────────────
(Asynchronous Processing in Background Worker)

[vm:listener on `shipment-milestone-queue`]
       │
       ▼
[Build HTML Email Content & Subject with DataWeave]
       │
       ▼
[choice: Check If Live SMTP Enabled (notification.email.enabled == 'true')]
       ├── YES ──► [Try Physical Email Dispatch via Email_SMTP (smtp.gmail.com:587)]
       └── NO  ──► [Log Full Rich Email Update in Studio Console (Simulation / Outbox)]
       │
       ▼
[subflow-mark-notification-sent]
       │  • Updates `notification_outbox` record: status = 'SENT', sent_at = NOW(3)
```

### 5.3 Configuration (`config/mule-dev.yaml`)
```yaml
notification:
  email:
    enabled: "false"                  # Set to "true" to send real live emails via SMTP
    host: "smtp.gmail.com"           # Or sandbox.smtp.mailtrap.io
    port: "587"
    user: "demo@gmail.com"
    password: "demo-app-password"    # Free Google App Password
    fromAddress: "alerts@controltower-logistics.com"
    defaultRecipient: "customer@control-tower-logistics.com"
    subjectPrefix: "[Control Tower Alert]"
```

---

## 6. Step-by-Step Process to Check Email Notifications

### Step 1: Start the Mule Application in Anypoint Studio
1. In Anypoint Studio, right-click `shipment-tracking-control-tower` -> **Run As -> Mule Application**.
2. Wait for the console message:
   ```text
   **********************************************************************
   * Application: shipment-tracking-control-tower                       *
   * OS encoding: UTF-8, Mule encoding: UTF-8                           *
   *                                                                    *
   * --- APPLICATION DEPLOYED ---                                       *
   **********************************************************************
   ```

### Step 2: Send a Milestone Webhook Scan in Postman
Send a `DELIVERED` scan for shipment `BD-987654321` to trigger milestone alert:
- **Method**: `POST`
- **URL**: `http://localhost:8081/api/v1/webhooks/carriers/BLUEDART`
- **Headers**:
  - `Content-Type: application/json`
  - `X-Carrier-Token: bluedart-webhook-secret-key-2026`
- **Body**:
  ```json
  {
    "awb": "BD-987654321",
    "status": "DL",
    "status_description": "Delivered to recipient",
    "scan_location": "Mumbai Hub",
    "scan_datetime": "2026-10-11T16:30:00Z"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "status": "SUCCESS",
    "message": "Tracking event processed and normalized successfully.",
    "trackingNumber": "BD-987654321",
    "canonicalStatus": "DELIVERED"
  }
  ```

### Step 3: Check Anypoint Studio Console Log
Look at the Studio console log. You will immediately see the asynchronous VM queue dispatch:
```text
================================================================================
[EMAIL NOTIFICATION DISPATCHED - ASYNCHRONOUS VM QUEUE & OUTBOX]
To: customer@control-tower-logistics.com
Subject: [Control Tower Alert] DELIVERED - BD-987654321
Milestone: DELIVERED
Tracking Number: BD-987654321
Carrier: BLUEDART
Message Body: Delivered successfully! Your shipment has been delivered at destination.
Outbox Status: SENT
================================================================================
```

### Step 3B: View Customer Message Directly in Postman
You can view the exact message generated for the customer right inside Postman:
- **Method**: `GET`
- **URL**: `http://localhost:8081/api/v1/shipments/BD-987654321/notifications`  
  *(Or: `{{baseUrl}}/shipments/{{trackingNumberBlueDart}}/notifications`)*
- **Headers**: None required
- **Body**: None
- **Expected Response (`200 OK`)**:
  ```json
  [
    {
      "id": 1,
      "notificationId": "NOTIF-79b8a2e1",
      "shipmentId": "SHP-1001",
      "trackingNumber": "BD-987654321",
      "carrier": "BLUEDART",
      "milestone": "DELIVERED",
      "messageBody": "Delivered successfully! Your shipment has been delivered at destination.",
      "channels": [
        "EMAIL"
      ],
      "status": "SENT",
      "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501",
      "createdAt": "2026-10-12T00:15:30Z",
      "sentAt": "2026-10-12T00:15:30Z"
    }
  ]
  ```

### Step 4: Verify in MySQL Database Outbox Table
Run this SQL query in MySQL Workbench:
```sql
SELECT notification_id, shipment_id, tracking_number, carrier, milestone, channels, status, sent_at 
FROM shipment_control_tower.notification_outbox 
ORDER BY id DESC LIMIT 5;
```
**Expected Output**:
```text
+-----------------+---------------+-----------------+----------+-----------+----------+--------+-------------------------+
| notification_id | shipment_id   | tracking_number | carrier  | milestone | channels | status | sent_at                 |
+-----------------+---------------+-----------------+----------+-----------+----------+--------+-------------------------+
| NOTIF-a1b2c3d4  | SHP-1001      | BD-987654321    | BLUEDART | DELIVERED | EMAIL    | SENT   | 2026-10-11 16:30:01.420 |
+-----------------+---------------+-----------------+----------+-----------+----------+--------+-------------------------+
```

### Step 5 (Optional): Sending Real Live Emails to an Actual Inbox
If you want real emails to arrive in an actual Gmail inbox or Mailtrap sandbox:
1. Open `src/main/resources/config/mule-dev.yaml`.
2. Set `notification.email.enabled: "true"`.
3. Provide your Gmail or Mailtrap SMTP credentials:
   - For Gmail: Go to Google Account -> Security -> 2-Step Verification -> **App Passwords** -> generate a 16-character password. Set `user` to your email and `password` to the App Password.
   - For Mailtrap (Zero Risk): Create a free account on [Mailtrap.io](https://mailtrap.io), copy the free Sandbox SMTP host (`sandbox.smtp.mailtrap.io`), port (`2525`), and username/password.
4. Save and re-run. Every milestone scan will physically appear in your real inbox!

---

## 7. Transitioning to Anypoint MQ in CloudHub

When deploying to multi-worker CloudHub 1.0 or CloudHub 2.0 clusters:
1. Replace `mule-vm-connector` with `anypoint-mq-connector:3.x`.
2. Create standard queues `prod-shipment-milestone-queue` and DLQ in **Anypoint Platform -> MQ**.
3. Point `config/mule-prod.yaml` to Anypoint MQ credentials (`anypoint.mq.clientId`, `anypoint.mq.clientSecret`).
4. Outbox table logic remains **100% identical**, providing multi-cloud broker independence!

