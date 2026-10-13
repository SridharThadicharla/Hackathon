# Shipment Signal Control Tower: Complete Master Project Guide

**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027  
**Track**: Use Case 08: Logistics – Real-Time Shipment Tracking  
**Application Name**: `shipment-tracking-control-tower`  
**Application Directory**: `Cognizant-Hackathon/Shipment-Signal-Control-Tower/`  
**Guides Directory**: `Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/`  

---

## Clickable Table of Contents

1. [00 – Start Here: Onboarding & Roadmap](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/00-START-HERE.md)
2. [01 – Project Overview & Business Context](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/01-Project-Overview.md)
3. [02 – Software Installation & Setup Guide](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/02-Software-Installation-and-Setup.md)
4. [03 – Anypoint Studio Project Import & Execution](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/03-Anypoint-Studio-Project-Import.md)
5. [04 – Architecture & API-Led Connectivity](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/04-Architecture-and-API-Led-Connectivity.md)
6. [05 – RAML 1.0 & APIKit Complete Guide](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/05-RAML-and-APIKit-Complete-Guide.md)
7. [06 – All Mule Flows Explained](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/06-All-Mule-Flows-Explained.md)
8. [07 – DataWeave 2.0 & Carrier Mappings](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/07-DataWeave-and-Carrier-Mappings.md)
9. [08 – MySQL Database Setup & Management](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/08-MySQL-Database-Setup.md)
10. [09 – Authentication & Security Guide](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/09-Authentication-and-Security.md)
11. [10 – Postman Complete Testing Guide](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/10-Postman-Complete-Testing-Guide.md)
12. [11 – MUnit Complete Testing Guide](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/11-MUnit-Complete-Testing-Guide.md)
13. [12 – Error Handling, Resilience & Retry](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/12-Error-Handling-and-Retry.md)
14. [13 – Queue & Notification Architecture](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/13-Queue-and-Notification-Guide.md)
15. [14 – Anypoint Platform & CloudHub Deployment](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/14-Anypoint-Platform-and-CloudHub-Deployment.md)
16. [15 – Logging, Observability & Troubleshooting](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/15-Logging-and-Troubleshooting.md)
17. [16 – Hackathon Live Demonstration Guide](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/16-Hackathon-Demo-Guide.md)
18. [17 – Judge Questions & Answers Architectural Defense](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/17-Judge-Questions-and-Answers.md)
19. [18 – Six-Member Team Responsibilities & RACI Matrix](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/18-Six-Member-Team-Responsibilities.md)
20. [19 – Requirements Traceability & Verification Checklist](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/19-Requirements-and-Verification-Checklist.md)
21. [20 – Project Limitations & Future Scope Roadmap](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/20-Project-Limitations-and-Future-Scope.md)
22. [Final Status Report](file:///c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment-Tracking-Complete-Guide/FINAL-STATUS-REPORT.md)

---

## 1. Executive Master Summary

The **Shipment Signal Control Tower** is a production-grade, event-driven logistics integration application engineered natively on MuleSoft Mule 4. It integrates with multi-carrier webhook push interfaces (supporting **BlueDart Express** and **Delhivery Logistics**), normalizes diverse schemas into a unified **Canonical Lifecycle Event Model**, enforces strict **idempotency**, guarantees **forward-only shipment status progression**, quarantines unmanifested tracking events with automated batch reconciliation, calculates an **Explainable Delay Risk Score** against promised customer delivery SLAs, and guarantees zero message loss using the **Transactional Notification Outbox Pattern** and persistent message queues.

---

## 2. System Architecture Blueprint

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        EXPERIENCE LAYER (X-APIs)                       │
│  - POST /webhooks/carriers/{carrierCode} (Secured via X-Carrier-Token) │
│  - POST /webhooks/bluedart & POST /webhooks/delhivery                  │
│  - GET /shipments/{trackingNumber}                                     │
│  - GET /shipments/{trackingNumber}/history                             │
│  - GET /shipments/{trackingNumber}/risk                                │
│  - GET /health & GET /carriers/pulse                                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         PROCESS LAYER (P-APIs)                         │
│  - DataWeave 2.0 Normalization (dw/bluedart-to-canonical.dwl, etc.)    │
│  - Idempotency Hashing (event_key = CARRIER-AWB-STATUS-COMPACTTS)      │
│  - Forward-Only State Machine (Status Rank 10 -> 20 -> 30 -> 40 -> 50) │
│  - Quarantine Buffer (pending_tracking_events) & /events/reconcile     │
│  - Explainable Delay Risk Engine (ON_TRACK, AT_RISK, DELAYED, CRITICAL)│
│  - Milestone Notification Filter (PICKED_UP, OFD, DELIVERED, EXCEPTION)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM LAYER (S-APIs)                          │
│  - MySQL 8.0 Relational Persistence (Database: shipment_control_tower) │
│    ├── shipments (Master state & SLA risk)                             │
│    ├── shipment_tracking_events (Immutable chronological audit trail)  │
│    ├── pending_tracking_events (Quarantine buffer for unmanifested)   │
│    ├── notification_outbox (Transactional outbox for alerts)           │
│    └── integration_alerts (Operational telemetry & SLA breaches)       │
│  - Asynchronous Message Broker (Persistent VM Queues / Anypoint MQ)   │
│    ├── shipment-milestone-queue (FIFO Persistent Queue)                │
│    └── shipment-milestone-dlq (Dead-Letter Queue)                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implemented Canonical Status Lifecycle

Every carrier event is normalized to one of the 9 official Use Case 08 lifecycle statuses:

```text
[LABEL_CREATED] (Rank 10)
       │
       ▼
  [PICKED_UP]   (Rank 20) ──► (Triggers Customer Milestone Alert)
       │
       ▼
  [IN_TRANSIT]  (Rank 30)
       │
       ▼
[ARRIVED_AT_HUB](Rank 35)
       │
       ▼
[OUT_FOR_DELIVERY](Rank 40) ──► (Triggers Customer Milestone Alert)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[DELIVERY_ATTEMPTED] (Rank 45)      [EXCEPTION] (Rank 42)
       │                                 │
       ▼                                 ▼
  [DELIVERED] (Rank 50 - Terminal)  [RETURNED] (Rank 60 - Terminal)
  (Triggers Milestone Alert)        (Triggers Milestone Alert)
```

---

## 4. End-to-End Execution Sequence

```text
HTTP Ingress Listener (/api/v1/webhooks/carriers/{carrierCode})
    │
    ▼
X-Correlation-ID Extraction or Auto-Generation
    │
    ▼
Carrier Authentication Check (X-Carrier-Token)
    │
    ▼
DataWeave 2.0 Normalizer to Canonical Event Model
    │
    ▼
Idempotency Query on Unique event_key in Database
    │
    ├── IF Duplicate Found:
    │   └── Suppress DB update & notifications -> Return HTTP 200 DUPLICATE_ACKNOWLEDGED
    │
    └── ELSE (Fresh Event):
        └── Master Shipment Lookup by tracking_number
            │
            ├── IF Unmanifested / Not Found:
            │   └── Insert into pending_tracking_events -> Return QUARANTINED_PENDING_REGISTRATION
            │
            └── IF Found:
                └── Evaluate Rank & Chronology
                    │
                    ├── IF Out-of-Order / Stale:
                    │   └── Insert to audit history as OUT_OF_ORDER_RECORDED
                    │   └── Do NOT regress master status -> Return OUT_OF_ORDER_RECORDED
                    │
                    └── ELSE (Normal Forward Progression):
                        └── Compute Risk Score & SLA Breach (risk-assessment.xml)
                        └── Update shipments master record
                        └── Insert into shipment_tracking_events as PROCESSED
                        └── Filter Milestone Notification
                            │
                            └── IF Milestone Eligible:
                                └── Insert into notification_outbox table (Status: QUEUED)
                                └── Publish to VM Queue (shipment-milestone-queue)
                                └── Asynchronous Consumer Dispatches & Marks Outbox SENT
                        └── Return HTTP 200 EVENT_PROCESSED_SUCCESSFULLY
```

---

## 5. Converting This Guide to PDF (`COMPLETE-PROJECT-GUIDE.pdf`)

To generate `COMPLETE-PROJECT-GUIDE.pdf` from this Markdown file, you can use any of the following standard approaches:

### Method 1: Using Node.js `md-to-pdf` or `markdown-pdf` (Recommended)
```powershell
# In terminal:
npx md-to-pdf COMPLETE-PROJECT-GUIDE.md
```

### Method 2: Using VS Code / IDE Markdown PDF Extension
1. Open `COMPLETE-PROJECT-GUIDE.md` in any markdown editor (VS Code, Obsidian, Typora).
2. Right-click and select **Markdown PDF: Export (pdf)**.

### Method 3: Using Chrome / Edge Browser Print to PDF
1. Open this file in any markdown viewer or browser.
2. Press `Ctrl + P` -> Select **Destination: Save as PDF** -> Click **Save**.
