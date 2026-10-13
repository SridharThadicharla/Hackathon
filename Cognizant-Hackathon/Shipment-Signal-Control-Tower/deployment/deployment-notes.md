# Deployment Guide & Notes – Shipment Signal Control Tower

## 1. Overview

This document specifies the deployment architecture and execution procedures for deploying the **Shipment Signal Control Tower** on local Anypoint Studio runtimes and enterprise MuleSoft targets (CloudHub 1.0, CloudHub 2.0, and Runtime Fabric).

---

## 2. Local Environment Deployment

### 2.1 Prerequisites
- **Java Development Kit (JDK)**: JDK 17 (Temurin-17 / Adoptium 17) or JDK 8/11 depending on exact Mule runtime selected.
- **Anypoint Studio**: Version 7.18+ or 7.27+ with embedded Mule 4 runtime (4.12.1 / 4.4.x).
- **MySQL Database**: MySQL Server 8.0 running locally on port 3306.
- **Postman**: Postman desktop client for running the test collection.

### 2.2 Execution Steps
1. Start local MySQL service: `net start MySQL80`
2. Create database and tables:
   ```powershell
   Get-Content -Path "database\schema.sql" -Raw | & mysql.exe -u root -proot
   Get-Content -Path "database\sample-data.sql" -Raw | & mysql.exe -u root -proot
   ```
3. Open Anypoint Studio and set workspace to `C:\Users\DELL\AnypointStudio\studio-workspace`.
4. Import project via **File -> Import -> Anypoint Studio -> Packaged mule application (.jar) or Existing Mule Project into Workspace**.
5. Select `Cognizant-Hackathon/Shipment-Signal-Control-Tower`.
6. Right-click on project -> **Run As -> Mule Application**.
7. Confirm log banner: `Mule is up and kicking` and HTTP listener listening on `0.0.0.0:8081`.

---

## 3. Packaging Application for Deployment

Run the standard Maven packaging command to build the deployable Mule application archive (`.jar`):

```powershell
mvn clean package -DskipTests
```

The resulting artifact is located at:
`target/shipment-tracking-control-tower-1.0.0-SNAPSHOT-mule-application.jar`

---

## 4. CloudHub 1.0 / 2.0 Deployment

### 4.1 Required Environment Properties in Anypoint Runtime Manager

When deploying to CloudHub, NEVER hardcode database passwords or carrier API tokens in cleartext files. Configure them as **Secure Application Properties** in Runtime Manager:

| Property Name | Example Value / Description | Sensitive? |
|---|---|---|
| `mule.env` | `prod` | No |
| `http.port` | `8081` | No |
| `db.host` | `rds-mysql-logistics.internal` | No |
| `db.port` | `3306` | No |
| `db.database` | `shipment_control_tower` | No |
| `db.user` | `control_tower_app` | No |
| `db.password` | `**********` | **YES (Protected Property)** |
| `carrier.bluedart.token` | `bluedart-webhook-secret-key-2026` | **YES (Protected Property)** |
| `carrier.delhivery.token` | `delhivery-webhook-secret-key-2026` | **YES (Protected Property)** |

### 4.2 CloudHub Maven Deployment Plugin Configuration

To deploy via CI/CD pipelines, configure the `mule-maven-plugin` with the CloudHub deployment descriptor:

```xml
<plugin>
    <groupId>org.mule.tools.maven</groupId>
    <artifactId>mule-maven-plugin</artifactId>
    <version>4.10.1</version>
    <extensions>true</extensions>
    <configuration>
        <cloudhub2Deployment>
            <uri>https://anypoint.mulesoft.com</uri>
            <provider>MC</provider>
            <environment>Production</environment>
            <target>Cloudhub-US-East-2</target>
            <muleVersion>4.12.0</muleVersion>
            <username>${env.ANYPOINT_USERNAME}</username>
            <password>${env.ANYPOINT_PASSWORD}</password>
            <applicationName>shipment-control-tower-prod</applicationName>
            <replicas>2</replicas>
            <vCores>0.2</vCores>
            <properties>
                <mule.env>prod</mule.env>
            </properties>
            <secureProperties>
                <db.password>${env.DB_PASSWORD}</db.password>
                <carrier.bluedart.token>${env.BLUEDART_TOKEN}</carrier.bluedart.token>
                <carrier.delhivery.token>${env.DELHIVERY_TOKEN}</carrier.delhivery.token>
            </secureProperties>
        </cloudhub2Deployment>
    </configuration>
</plugin>
```
