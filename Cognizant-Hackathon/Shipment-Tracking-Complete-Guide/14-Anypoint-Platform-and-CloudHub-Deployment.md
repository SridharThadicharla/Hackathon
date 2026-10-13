# 14 – Anypoint Platform & CloudHub Deployment Guide

**Project**: Shipment Signal Control Tower  
**Target Platform**: MuleSoft Anypoint Platform (Runtime Manager)  
**Deployment Targets**: CloudHub 1.0 / CloudHub 2.0 (Shared & Private Spaces)  

---

## 1. What is Anypoint Platform?

**Anypoint Platform** is MuleSoft's unified enterprise iPaaS (Integration Platform as a Service). It includes:
- **Design Center**: Collaborative API specification modeling and mocking.
- **Anypoint Exchange**: Central catalog of APIs, connectors, and reusable templates.
- **API Manager**: Gateway governance, SLA tier management, and security policies.
- **Runtime Manager**: Management control plane for deploying, monitoring, scaling, and logging Mule applications running on CloudHub or customer infrastructure.

---

## 2. CloudHub 1.0 vs. CloudHub 2.0: Key Differences

| Feature | CloudHub 1.0 (AWS EC2 / Workers) | CloudHub 2.0 (Kubernetes / Replicas) |
|---|---|---|
| **Architecture** | Dedicated Amazon EC2 virtual instances per worker | Containerized micro-VM pods managed on Kubernetes |
| **Compute Units** | Workers (0.1, 0.2, 1, 2 vCores) | Replicas (0.1, 0.2, 0.5, 1, 2 vCores) |
| **Networking** | CloudHub VPC, Dedicated Load Balancer (DLB), VPN | Shared Spaces (Multi-tenant) or Private Spaces (VPC Peering/Transit Gateway) |
| **URL Format** | `http(s)://<app-name>.<region>.cloudhub.io` | `http(s)://<app-name>.<unique-hash>.<region>.cloudhub.io` |
| **Log Management** | Built-in CloudHub 1.0 log streaming | Built-in Log streaming with Anypoint Monitoring telemetry |

> [!NOTE]
> Choose your deployment target based on your organization's subscription access. Both targets are fully supported by this Mule application package!

---

## 3. Preparing the Deployable Package

Before deploying, build the production-ready deployable Mule archive (`.jar`):

```powershell
mvn clean package -DskipTests
```

Verify that the target JAR is generated at:
`Cognizant-Hackathon/Shipment-Signal-Control-Tower/target/shipment-tracking-control-tower-1.0.0-SNAPSHOT-mule-application.jar`

---

## 4. Deploying via Runtime Manager Web UI (Step-by-Step)

### Step 1: Log in to Anypoint Platform
1. Open your browser and navigate to [https://anypoint.mulesoft.com](https://anypoint.mulesoft.com).
2. Enter your credentials or log into your 30-day Anypoint Platform Trial account.
3. Select your designated Environment (e.g. `Sandbox` or `Production`).

### Step 2: Open Runtime Manager
1. In the top-left navigation burger menu, click **Runtime Manager**.
2. Click the blue button: **Deploy Application**.

### Step 3: Configure Application Settings
1. **Application Name**: Enter a globally unique name, for example:
   `cognizant-shipment-tower-dev`
2. **Deployment Target**:
   - For CloudHub 1.0: Select **CloudHub**.
   - For CloudHub 2.0: Select **CloudHub 2.0** and pick **Shared Space: us-east-2** (or your region).
3. **Application File**: Click **Choose File -> Upload file** and select:
   `target/shipment-tracking-control-tower-1.0.0-SNAPSHOT-mule-application.jar`.
4. **Runtime Version**: Select `4.12.0` or `4.4.x` (matching application descriptor).
5. **Worker / Replica Size**: Select `0.1 vCore` or `0.2 vCore`.
6. **Workers**: `1` (for dev / demo testing).

### Step 4: Configure Application Properties
Click the **Properties** tab. Enter the required connection properties:

```properties
mule.env=dev
http.port=8081
db.host=<your-cloud-mysql-endpoint-or-aws-rds-hostname>
db.port=3306
db.database=shipment_control_tower
db.user=tower_admin
carrier.bluedart.token=bluedart-webhook-secret-key-2026
carrier.delhivery.token=delhivery-webhook-secret-key-2026
queue.provider=vm
queue.milestoneQueue=shipment-milestone-queue
queue.deadLetterQueue=shipment-milestone-dlq
```

### Step 5: Protect Sensitive Properties
In the **Properties** tab:
1. Mark `db.password` as a protected property.
2. Enter your MySQL database password.
3. Click **Protect**. The value will be masked with asterisks and hidden from UI viewers.

### Step 6: Deploy & Monitor Startup
1. Click **Deploy Application**.
2. In the Applications list, monitor the status pill:
   `Undeployed -> Deploying -> Started (Green Circle)`.
3. Click on the application name and open the **Logs** tab.
4. Look for the startup confirmation:
   `Application 'cognizant-shipment-tower-dev' has started successfully.`

---

## 5. Testing the Cloud Deployed Endpoint in Postman

1. Copy the public **App URL** from Runtime Manager, for example:
   `http://cognizant-shipment-tower-dev.us-e2.cloudhub.io`
2. In Postman, edit the `baseUrl` environment variable:
   `baseUrl = http://cognizant-shipment-tower-dev.us-e2.cloudhub.io/api/v1`
3. Execute the `GET Operational Health Check` request:
   `GET {{baseUrl}}/health`
4. Confirm HTTP `200 OK`:
   ```json
   {
     "status": "UP",
     "service": "Shipment Signal Control Tower API",
     "version": "1.0.0",
     "database": "CONNECTED",
     "queue": "CONNECTED"
   }
   ```

---

## 6. Cloud Database Connectivity Considerations

When deploying to CloudHub, your local `localhost:3306` MySQL server is unreachable from the public internet:
1. **Option A (AWS RDS MySQL)**: Create a free-tier Amazon RDS MySQL instance, make it publicly accessible with a security group allowing inbound port 3306 from CloudHub, and set `db.host = <rds-endpoint>`.
2. **Option B (CloudHub VPC Peering)**: For enterprise deployments, peer the CloudHub VPC directly with your internal corporate AWS VPC.
3. **Option C (Local Testing)**: Use local Anypoint Studio execution pointing to local MySQL 8.0, and present the CloudHub configuration as the enterprise deployment pathway for judges.
