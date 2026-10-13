# 04 – Installation & Project Startup Runbook (Anypoint Studio)

**Target Environment**: Local Developer Workstation  
**Development IDE**: Anypoint Studio 7.14+ (Mule Runtime 4.4.0 Enterprise Edition)  
**Database**: MySQL Server 8.0 (localhost:3306)  
**JDK Requirement**: OpenJDK 8 (AdoptOpenJDK 1.8) or OpenJDK 11 (Zulu/Temurin 11)  

---

## 1. Prerequisites & Environment Compatibility

Before launching the project, verify that the required software is installed and running:

| Component | Verified Version | Purpose | Verification Command / Check |
|---|---|---|---|
| **Anypoint Studio** | 7.14.0 or higher | Official MuleSoft Eclipse-based IDE | Check **Help -> About Anypoint Studio** |
| **Mule Runtime** | 4.4.0 EE | Embedded execution engine | Included with Anypoint Studio 7.14+ |
| **Java JDK** | Java 8 (1.8.0_352) or Java 11 (11.0.17) | Compilation & Mule runtime execution | Run in terminal: `java -version` |
| **MySQL Server** | MySQL 8.0 | Systems of record persistence | Run in terminal: `mysql --version` (or verify MySQL service in Windows Services) |
| **Postman** | Postman Desktop v10+ | API evaluation & manual execution | Open Postman application |

> [!WARNING]
> **Java Version Compatibility**: Mule Runtime 4.4.0 does **not** support Java 17, 21, or 22 for compilation. Ensure Anypoint Studio is pointed to a valid JDK 8 or JDK 11 under **Preferences -> Java -> Installed JREs**.

---

## 2. Step 1: Database Initialization (MySQL 8.0)

The application requires the database `shipment_control_tower` with all five relational tables and sample seed records before it can process tracking requests.

1. Open **MySQL Workbench** or Windows Command Prompt / PowerShell.
2. Connect to your local MySQL instance:
   ```powershell
   mysql -u root -p
   ```
3. Execute the schema script located at [database/schema.sql](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/database/schema.sql):
   ```sql
   source Cognizant-Hackathon/Shipment-Signal-Control-Tower/database/schema.sql;
   ```
   *(This creates database `shipment_control_tower` and drops/recreates all tables cleanly).*

4. Execute the seed data script located at [database/sample-data.sql](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/database/sample-data.sql):
   ```sql
   source Cognizant-Hackathon/Shipment-Signal-Control-Tower/database/sample-data.sql;
   ```
   *(This seeds test shipments `SHP-1001` through `SHP-1005` and baseline outbox entries).*

5. Verify that tables exist:
   ```sql
   USE shipment_control_tower;
   SHOW TABLES;
   ```
   *Expected Output*:
   - `integration_alerts`
   - `notification_outbox`
   - `pending_tracking_events`
   - `shipment_tracking_events`
   - `shipments`

---

## 3. Step 2: Importing Project into Anypoint Studio

1. Launch **Anypoint Studio**.
2. Select your designated workspace directory (e.g., `C:\Users\DELL\AnypointStudio\workspace`).
3. In the top menu, navigate to:
   **File -> Import...**
4. Expand the **Anypoint Studio** folder and select:
   **Anypoint Studio -> Packaged mule application (.jar) or Anypoint Studio project from File System**.
5. Click **Next**.
6. In **Project Root**, click **Browse...** and select the project folder:
   `c:\Users\DELL\OneDrive\Desktop\Hackathon11\Cognizant-Hackathon\Shipment-Signal-Control-Tower\`
7. Ensure **Server Runtime** is set to **Mule Server 4.4.0 EE**.
8. Click **Finish**.
9. Allow Anypoint Studio 1–2 minutes to resolve Maven dependencies from the MuleSoft Enterprise repository.

---

## 4. Step 3: Configuring Local Properties (`mule-dev.yaml`)

Open [src/main/resources/config/mule-dev.yaml](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/resources/config/mule-dev.yaml) in Anypoint Studio:

```yaml
http:
  host: "0.0.0.0"
  port: "8081"
  basePath: "/api/v1"

# Database Configuration (MySQL 8.0)
db:
  host: "localhost"
  port: "3306"
  user: "root"
  password: "YOUR_DB_PASSWORD"          # Replace with your local MySQL password
  database: "shipment_control_tower"
  connectionTimeout: "30000"

# Carrier Webhook Authentication (Shared Secrets / API Tokens)
carrier:
  bluedart:
    token: "bluedart-webhook-secret-key-2026"
  delhivery:
    token: "delhivery-webhook-secret-key-2026"

# Milestone Notification Queue Settings
queue:
  provider: "vm"
  milestoneQueue: "shipment-milestone-queue"
  deadLetterQueue: "shipment-milestone-dlq"

# Explainable Risk Engine Thresholds (Hours)
risk:
  staleTransitHours: "48"
  criticalExceptionHours: "24"
  warningLeadHours: "6"

# Email Notification Gateway Configuration (Optional Real Email Dispatch)
notification:
  email:
    enabled: "false"                    # Set to "true" to enable real SMTP dispatch
    host: "smtp.gmail.com"
    port: "587"
    user: "YOUR_EMAIL@gmail.com"
    password: "YOUR_16_CHAR_APP_PASSWORD"
    fromAddress: "YOUR_EMAIL@gmail.com"
    defaultRecipient: "YOUR_EMAIL@gmail.com"
    subjectPrefix: "[Control Tower Alert]"
```

> [!NOTE]
> When `notification.email.enabled` is `"false"`, the application simulates email dispatch in the Studio console log, ensuring zero runtime dependencies on an active internet connection.

---

## 5. Step 4: Starting the Mule Application

1. In the **Package Explorer** view on the left, right-click the project:
   `Shipment-Signal-Control-Tower`
2. Select:
   **Run As -> Mule Application**
3. The **Console** view will open at the bottom of the screen.
4. Watch the deployment log stream. Within 15–30 seconds, you should see:
   ```text
   INFO  ... [HTTP_Listener_config] Initializing HTTP Listener on host: 0.0.0.0, port: 8081
   INFO  ... [Database_Config] Initialized MySQL Database connection pool
   INFO  ... [VM_Config] Initialized persistent FIFO queues: shipment-milestone-queue, shipment-milestone-dlq
   **********************************************************************
   * Application: shipment-tracking-control-tower                       *
   * OS-Architecture: amd64                                             *
   * Running in: Anypoint Studio                                        *
   * Status: DEPLOYED                                                   *
   **********************************************************************
   ```

---

## 6. Step 5: Verification of Ready State

Once deployed, run a health check verification to prove all subsystems are operational:

1. Open your browser or Postman.
2. Send a `GET` request to:
   `http://localhost:8081/api/v1/health`
3. Expected JSON response (`HTTP 200 OK`):
   ```json
   {
     "status": "UP",
     "service": "Shipment Signal Control Tower API",
     "version": "1.0.0",
     "environment": "dev",
     "database": "CONNECTED",
     "queue": "CONNECTED",
     "timestamp": "2026-10-13T12:00:00Z"
   }
   ```
4. Also open the interactive **APIKit Console**:
   `http://localhost:8081/console/`
   *(Verifies that the RAML specification and all interactive endpoints are ready).*

---

## 7. Step 6: Safe Shutdown and Restart

- **To Stop**: Click the red square **Terminate** button located in the top-right toolbar of the Studio Console view.
- **To Restart**: Right-click the project -> **Run As -> Mule Application** (or press `Ctrl + F11`).
