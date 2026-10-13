# 03 – Anypoint Studio Project Import & Execution Guide

**Project**: Shipment Signal Control Tower  
**Development Tool**: Anypoint Studio 7.27.0  
**Project Location**: `Cognizant-Hackathon/Shipment-Signal-Control-Tower`  

---

## 1. Opening Anypoint Studio & Selecting Workspace

1. Launch Anypoint Studio from `C:\AnypointStudio\AnypointStudio.exe`.
2. In the **Workspace Launcher** dialog:
   - Workspace: Enter `C:\Users\DELL\AnypointStudio\studio-workspace`
   - Check *Use this as the default and do not ask again* (optional).
   - Click **Launch**.
3. Anypoint Studio initializes the Eclipse-based IDE workbench.

---

## 2. Importing the Project Step-by-Step

Follow these exact steps to import the Mule application:

### Step 1: Open the Import Wizard
- In the top menu bar, click **File -> Import...** (or right-click in the *Package Explorer* view and select **Import...**).

### Step 2: Select the Import Source
- In the Import wizard dialog, expand the folder labeled **Anypoint Studio**.
- Select **Anypoint Studio project from File System**.
- Click **Next >**.

```text
Import
  Select an import wizard:
  ▼ Anypoint Studio
      Anypoint Studio project from File System   ◄── [SELECT THIS]
      Packaged mule application (.jar)
```

### Step 3: Browse to Project Root
- Next to **Project Root**, click **Browse...**.
- Navigate to:
  `C:\Users\DELL\OneDrive\Desktop\Hackathon11\Cognizant-Hackathon\Shipment-Signal-Control-Tower`
- Click **Select Folder**.
- Studio automatically reads `.project` and `pom.xml` and detects:
  - **Project Name**: `Shipment-Signal-Control-Tower`
  - **Server Runtime**: `Mule Server 4.12.1 EE` (or your installed default Mule 4 runtime).

> [!NOTE]
> **Why the "Finish" button is now active**:
> Anypoint Studio is built on Eclipse, which requires the `.project` and `.classpath` metadata descriptors in the project root to recognize an unbundled directory. We have configured `.project`, `.classpath`, and `.settings/org.eclipse.core.resources.prefs`. If you had the Import dialog open previously, simply click **Cancel**, re-open **File -> Import -> Anypoint Studio -> Anypoint Studio project from File System**, and re-select the folder. The project will now be listed and **Finish** will be clickable!

### Step 4: Finish and Initial Build
- Check the option: **Copy project into workspace** (recommended to keep the original clean) OR leave unchecked to work directly on the folder.
- Click **Finish**.
- In the bottom-right corner of Studio, observe the progress bar:
  `Building workspace (Fetching Maven dependencies...)`
  Wait 15–30 seconds for Maven to finish indexing connectors.

---

### Alternative Import Method (Packaged Application Archive)
If you ever prefer importing directly from the compiled Mule deployable package:
1. Go to **File -> Import...**.
2. Select **Anypoint Studio -> Packaged mule application (.jar)** and click **Next >**.
3. In **Mule Application File**, browse to:
   `C:\Users\DELL\OneDrive\Desktop\Hackathon11\Cognizant-Hackathon\Shipment-Signal-Control-Tower\target\shipment-tracking-control-tower-1.0.0-SNAPSHOT-mule-application.jar`
4. Click **Finish**. Studio will automatically extract and configure the entire project.

---

## 3. Project Structure in Package Explorer

Once imported, expand `shipment-tracking-control-tower` in the **Package Explorer** view:

```text
shipment-tracking-control-tower/
├── src/main/mule/                          # Mule XML Flows & Configurations
│   ├── global-config.xml                   # HTTP Listener, MySQL & VM Queue configs
│   ├── webhook-api.xml                     # APIKit Ingress & Endpoint Routers
│   ├── carrier-normalization.xml           # BlueDart & Delhivery normalizer subflows
│   ├── shipment-processing.xml             # Deduplication, progression, quarantine
│   ├── risk-assessment.xml                 # SLA delay & explainable risk engine
│   ├── notification-queue.xml              # Outbox persistence & VM consumer
│   ├── database-operations.xml             # Parameterized SQL database subflows
│   └── error-handling.xml                  # Global application error handlers
├── src/main/resources/
│   ├── api/shipment-tracking.raml          # RAML 1.0 API specification
│   ├── config/mule-dev.yaml                # Development configuration properties
│   ├── config/mule-prod.yaml               # Production configuration template
│   ├── dw/bluedart-to-canonical.dwl        # DataWeave 2.0 BlueDart transformation
│   ├── dw/delhivery-to-canonical.dwl       # DataWeave 2.0 Delhivery transformation
│   ├── examples/                           # JSON mock payload examples
│   └── log4j2.xml                          # Logging configuration
├── src/test/munit/
│   └── shipment-tracking-test-suite.xml    # 9 Automated MUnit test cases
├── database/                               # MySQL schema & verification scripts
├── postman/                                # Postman test collection & environment
├── mule-artifact.json                      # Mule runtime descriptor
└── pom.xml                                 # Maven POM with connectors & plugins
```

---

## 4. Resolving Build Warnings & Problems

If Studio displays a red error indicator on `pom.xml` or XML files:

1. **Update Maven Project Dependencies**:
   - Right-click `shipment-tracking-control-tower` in Package Explorer.
   - Click **Mule -> Update Project Dependencies**.
2. **Clean Project**:
   - In top menu, click **Project -> Clean...**.
   - Select `shipment-tracking-control-tower` and click **Clean**.
3. **Check the Problems Tab**:
   - Click the **Problems** tab at the bottom of the workbench.
   - Any remaining yellow warnings (such as `Connection is not secure. Should use HTTPS`) are informational and do not block local execution.

---

## 5. Starting the Application Locally

1. Right-click on the project root `shipment-tracking-control-tower` in Package Explorer.
2. Select **Run As -> Mule Application** (or press `Alt + Shift + X, M`).
3. The **Console** view opens automatically.

### 5.1 What Success Looks Like in Console Logs
Watch the console output. Look for these two definitive milestones:

```text
INFO  2026-10-11 11:46:20 [main] org.mule.service.http.impl.service.server.grizzly.GrizzlyServerManager: 
Listening for HTTP requests on /0.0.0.0:8081

**********************************************************************
* Application: shipment-tracking-control-tower                       *
* OS-Architecture: amd64                                             *
* Running in: org.mule.runtime.core.internal.context.DefaultMuleCtx  *
* Mule is up and kicking                                             *
**********************************************************************

INFO  2026-10-11 11:46:25 [main] org.mule.runtime.core.internal.lifecycle.DefaultLifecycleManager: 
Application 'shipment-tracking-control-tower' has started successfully.
```

When you see **`Mule is up and kicking`**, your application is running and actively listening on port `8081`!

---

## 6. Stopping & Restarting the Application

- **To Stop**: Click the red square **Terminate** button located on the top-right toolbar of the **Console** view.
- **To Restart**: Click the green circular **Run** icon in the main toolbar, or right-click project -> **Run As -> Mule Application**.
- **To Debug**: Right-click project -> **Debug As -> Mule Application**. Double-click on any message processor in the visual canvas to place a breakpoint and step through payload states in real-time.
