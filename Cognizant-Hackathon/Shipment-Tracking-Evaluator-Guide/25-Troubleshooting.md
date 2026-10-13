# 25 – Project Troubleshooting & Live Incident Recovery Runbook

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0)  

---

## 1. Quick Incident Index

| Symptom / Error Message | Likely Root Cause | Immediate Safe Fix |
|---|---|---|
| `Address already in use: JVM_Bind (Port 8081)` | Another application or previous Mule instance is running. | Kill process on port 8081 via PowerShell or change port in `mule-dev.yaml`. |
| `Cannot resolve dependency ... org.mule.connectors` | Maven proxy or local `.m2` repository cache corruption. | Run `mvn clean install -U` or re-download in Anypoint Studio. |
| `Communications link failure / Connection refused (Port 3306)` | MySQL 8.0 server service stopped. | Start MySQL service via `net start MySQL80` or Services console. |
| `Access denied for user 'root'@'localhost'` | Incorrect MySQL password in `mule-dev.yaml`. | Update `db.password` in [mule-dev.yaml](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Signal-Control-Tower/src/main/resources/config/mule-dev.yaml). |
| `[Out-of-Order] Stale/Older event received... Preserving DELIVERED` | Sample shipment was already delivered in earlier test runs. | Re-seed database using `database/sample-data.sql` to reset status. |
| `AuthenticationFailedException (535-5.7.8)` on SMTP send | Using standard Google password instead of 16-character App Password. | Generate dedicated Google App Password in Google Account Security. |
| `Java version mismatch / Compilation failure` | Anypoint Studio using Java 17+ instead of Java 8/11. | Set installed JRE to OpenJDK 8 or 11 in Studio Preferences. |

---

## 2. In-Depth Incident Diagnostics & Resolution

### Incident 1: HTTP Port 8081 Conflict
- **Symptom**: Console displays `java.net.BindException: Address already in use: bind`.
- **Cause**: An earlier instance of the Mule application was not terminated cleanly.
- **Resolution**:
  1. Open PowerShell as Administrator.
  2. Find the PID listening on port 8081:
     ```powershell
     Get-NetTCPConnection -LocalPort 8081 | Select-Object OwningProcess
     ```
  3. Terminate the process:
     ```powershell
     Stop-Process -Id <PID> -Force
     ```
  4. Alternatively, open `mule-dev.yaml` and temporarily set `http.port: "8082"`.

---

### Incident 2: MySQL Connection Refused
- **Symptom**: `org.mule.runtime.api.connection.ConnectionException: Cannot get connection for URL jdbc:mysql://localhost:3306/shipment_control_tower`.
- **Cause**: Local MySQL Server service is stopped.
- **Resolution**:
  1. Open Windows PowerShell and run:
     ```powershell
     Start-Service -Name "MySQL80"
     ```
  2. Test database accessibility:
     ```powershell
     & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "SELECT 1;"
     ```

---

### Incident 3: Test Webhook Returns `OUT_OF_ORDER_RECORDED` Instead of Sending Email
- **Symptom**: Log displays: `[Out-of-Order] Stale/Older event received for Shipment SHP-1002. Preserving in history without regressing current status: DELIVERED`.
- **Cause**: The shipment was previously progressed all the way to `DELIVERED` (Rank 50). The Anti-Regression engine protects delivered shipments from being downgraded to `OUT_FOR_DELIVERY` (Rank 40).
- **Resolution**:
  Reset the database back to its initial baseline by piping `sample-data.sql` into MySQL:
  ```powershell
  Get-Content "Cognizant-Hackathon\Shipment-Signal-Control-Tower\database\sample-data.sql" | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -proot shipment_control_tower
  ```
  Now `SHP-1001` is `LABEL_CREATED` (Rank 10) and `SHP-1002` is `PICKED_UP` (Rank 20), ready for milestone processing!

---

### Incident 4: SMTP Email Authentication Error (Gmail)
- **Symptom**: `[Live Email Warning] Could not connect to external SMTP server: 535-5.7.8 Username and Password not accepted`.
- **Cause**:
  1. Standard Gmail login password used instead of a 16-character **Google App Password**.
  2. `fromAddress` in `mule-dev.yaml` does not match the authenticated Gmail account.
- **Resolution**:
  1. Go to [Google Account Security](https://myaccount.google.com/security).
  2. Ensure 2-Step Verification is ON $\rightarrow$ create an **App Password** for `MuleSoft`.
  3. In `mule-dev.yaml`:
     ```yaml
     notification:
       email:
         enabled: "true"
         host: "smtp.gmail.com"
         port: "587"
         user: "YOUR_GMAIL@gmail.com"
         password: "YOUR_16_CHAR_APP_PASSWORD"
         fromAddress: "YOUR_GMAIL@gmail.com"
         defaultRecipient: "YOUR_GMAIL@gmail.com"
     ```
