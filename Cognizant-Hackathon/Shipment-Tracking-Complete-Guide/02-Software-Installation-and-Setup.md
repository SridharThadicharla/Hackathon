# 02 – Software Installation & Setup Guide

**Project**: Shipment Signal Control Tower  
**Target Environment**: Windows 11 / 64-bit  
**MuleSoft Runtime**: Mule 4.12.1 / Mule 4.4.x  

---

## 1. Required Software Stack

| Component | Verified Version | Purpose | Download Source |
|---|---|---|---|
| **Java JDK** | OpenJDK 17.0.20 (Temurin-17) | Core Java runtime for Mule 4.12 / 4.4 and Maven | [Adoptium Temurin 17](https://adoptium.net/) |
| **Anypoint Studio** | 7.27.0 (Eclipse 4.31 base) | Official MuleSoft IDE for visual and XML development | [MuleSoft Studio Downloads](https://www.mulesoft.com/platform/studio) |
| **Apache Maven** | 3.9.4 or 3.9.x | Build and dependency management engine | [Apache Maven](https://maven.apache.org/download.cgi) |
| **MySQL Server** | MySQL Community Server 8.0 | Relational database for master shipments, events & outbox | [MySQL Community 8.0](https://dev.mysql.com/downloads/mysql/) |
| **MySQL Workbench** | 8.0 CE | GUI client for database inspection and query execution | [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) |
| **Postman** | Postman Desktop v10+ | API client for running test collections and webhooks | [Postman Download](https://www.postman.com/downloads/) |

---

## 2. Step-by-Step Software Installation

### Step 2.1: Java Development Kit (JDK 17) Setup
1. Download **Eclipse Temurin JDK 17 (x64 Installer)** (`.msi`).
2. Run the installer and ensure the following features are enabled:
   - *Set JAVA_HOME variable* -> Select "Will be installed on local hard drive".
   - *Add to PATH* -> Select "Will be installed on local hard drive".
3. Verify installation in PowerShell:
   ```powershell
   java -version
   ```
   *Expected Output*:
   ```text
   openjdk version "17.0.20" 2026-07-21
   OpenJDK Runtime Environment Temurin-17.0.20+8 (build 17.0.20+8)
   OpenJDK 64-Bit Server VM Temurin-17.0.20+8 (build 17.0.20+8, mixed mode, sharing)
   ```

### Step 2.2: Apache Maven Setup
1. Download `apache-maven-3.9.4-bin.zip`.
2. Extract to `C:\apache-maven-3.9.4` (or use the Maven bundled in Mule tooling extensions at `C:\Users\DELL\.vscode\extensions\salesforce.mule-dx-dependencies-1.7.1-win32-x64\build\deps\apache-maven-3.9.4\bin`).
3. Add the `bin` directory to your system `PATH` environment variable.
4. Verify Maven installation:
   ```powershell
   mvn -version
   ```
   *Expected Output*:
   ```text
   Apache Maven 3.9.4
   Maven home: C:\apache-maven-3.9.4
   Java version: 17.0.20, vendor: Eclipse Adoptium
   ```

### Step 2.3: Anypoint Studio 7.27 Setup
1. Extract the downloaded `AnypointStudio-7.27.0-win64.zip` to `C:\AnypointStudio`.
2. Inspect `C:\AnypointStudio\AnypointStudio.ini` to verify embedded VM configuration:
   ```ini
   -vm
   plugins/org.mule.tooling.jdk.win32.x86_64_1.4.1/bin/javaw.exe
   -Dosgi.instance.area.default=@user.home/AnypointStudio/studio-workspace
   -Xms512m
   -Xmx1024m
   ```
3. Double click `C:\AnypointStudio\AnypointStudio.exe` to launch the IDE.
4. When prompted for the workspace directory, enter:
   `C:\Users\DELL\AnypointStudio\studio-workspace`

### Step 2.4: MySQL 8.0 Server Setup
1. Install MySQL Server 8.0 using the MySQL Installer.
2. During configuration:
   - Port: `3306`
   - Default Authentication: "Use Strong Password Encryption (Recommended)"
   - Root Password: Set to `root` (or configured value matching `config/mule-dev.yaml`)
   - Windows Service Name: `MySQL80` (ensure "Start the MySQL Server at System Startup" is checked).
3. Verify the service is running in PowerShell:
   ```powershell
   Get-Service -Name "MySQL80"
   ```
   *Expected Output*:
   ```text
   Status   Name      DisplayName
   ------   ----      -----------
   Running  MySQL80   MySQL80
   ```

---

## 3. Configuring Anypoint Studio Preferences

To ensure Anypoint Studio builds and executes Mule 4 projects without dependency or JVM resolution errors:

### 3.1 Configure Installed JREs
1. In Studio menu, click **Window -> Preferences**.
2. Navigate to **Java -> Installed JREs**.
3. Verify that **Temurin-17** (or the bundled `org.mule.tooling.jdk`) is selected as the default JRE.

### 3.2 Configure Embedded Maven in Studio
1. In Studio Preferences, navigate to **Anypoint Studio -> Maven**.
2. Select **Use embedded Maven** (or point to `apache-maven-3.9.4`).
3. Check the box: **Override settings.xml directory** if using a custom Maven repository config.
4. Click **Test Maven Configuration**. Ensure a green checkmark appears: `Maven configuration is valid`.

---

## 4. Common Setup Errors & Instant Fixes

### Error 1: "Access denied for user 'root'@'localhost'"
- **Cause**: MySQL password mismatch.
- **Fix**: Open `config/mule-dev.yaml` and update `db.password` to match your local MySQL root password. Alternatively, reset root password in MySQL Command Line:
  `ALTER USER 'root'@'localhost' IDENTIFIED BY 'root'; FLUSH PRIVILEGES;`

### Error 2: "Address already in use: bind :8081"
- **Cause**: Another service or previous Mule process is listening on port 8081.
- **Fix**: Identify the process using PowerShell:
  `Get-NetTCPConnection -LocalPort 8081 | Select-Object OwningProcess`
  Terminate the lingering process via Task Manager or `Stop-Process -Id <PID>`.

### Error 3: "Failed to read artifact descriptor for mule-runtime-impl-bom"
- **Cause**: Running `mvn test` directly from CLI when MuleSoft Enterprise EE credentials are not configured in `settings.xml`.
- **Fix**: Run MUnit tests inside Anypoint Studio via **Right click -> Run As -> MUnit Suite**. Studio uses its pre-installed embedded Mule runtime without needing external repository credentials.
