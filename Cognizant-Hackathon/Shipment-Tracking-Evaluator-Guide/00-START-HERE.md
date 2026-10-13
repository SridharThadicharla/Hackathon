# 00 – Start Here: Evaluator Preparation Navigation Guide

**Project**: Shipment Signal Control Tower — Real-Time Multi-Carrier Shipment Tracking  
**Application**: `Shipment-Signal-Control-Tower` (Mule 4.4.0)  
**Hackathon**: Cognizant MuleSoft Hackathon 2026–2027 (Use Case 08)  

---

## 1. What This Documentation Suite Is For

This documentation folder is an authoritative, end-to-end knowledge base built specifically to prepare you for a **10–15 minute technical interview and project evaluation** before senior architects and hackathon judges.

During the interview, evaluators will assess:
1. **Architectural Clarity**: Can you explain why the system is designed this way?
2. **Codebase Mastery**: Do you know exactly which flow, connector, and DataWeave file executes each business requirement?
3. **Resilience & Edge Cases**: What happens when a webhook is duplicated, out-of-order, or an unknown tracking number arrives?
4. **Honesty & Precision**: Can you clearly state what is implemented and verified versus what is recommended for production?

This guide gives you the precise facts, code references, and ready-to-speak answers needed to score in the highest percentile.

---

## 2. Status Label Conventions Used Across This Guide

To ensure 100% technical integrity and prevent misleading an evaluator, every feature in this guide is labeled with one of the following exact statuses:

| Status Label | Meaning | Candidate Interview Guidance |
|---|---|---|
| **IMPLEMENTED AND VERIFIED** | The code exists in the repository, builds without error, and has been verified via automated MUnit tests or live manual Postman runs. | Speak with complete confidence. Cite flow names and test evidence. |
| **IMPLEMENTED — NOT VERIFIED** | The code and XML configurations exist in the project, but have not undergone dedicated live end-to-end verification (e.g., CloudHub auto-discovery). | State: *"The XML configuration and policy bindings are fully implemented in code, but live runtime verification in a CloudHub cluster is staged for production."* |
| **PARTIALLY IMPLEMENTED** | A foundational component exists (e.g., local VM queue or local SMTP toggle), but enterprise-scale extensions (like multi-region Anypoint MQ or external SMS gateways) are simulated. | Clearly articulate the implemented foundation and how it cleanly transitions to enterprise scale. |
| **NOT IMPLEMENTED** | The feature was mentioned in conceptual discussions or high-level requirements, but does not exist in the codebase. | State honestly: *"That capability is outside the current prototype scope and is documented in our Future Scope roadmap."* Evaluators respect this integrity. |
| **DESIGN RECOMMENDATION** | Best practices, architectural patterns, or production hardening steps that are not part of the active code. | Present as forward-looking architectural insight. |

---

## 3. Best Reading Order Based on Available Preparation Time

### Plan A: "Emergency Rehearsal" (15 Minutes Available Before Panel)
If your interview is starting in 15 minutes, focus exclusively on these three files:
1. **[28-Quick-Revision-Cheat-Sheet.md](28-Quick-Revision-Cheat-Sheet.md)** (5 min): Review the 2-page master cheat sheet containing core flow names, tables, and top 10 rapid-fire answers.
2. **[24-15-Minute-Interview-Preparation.md](24-15-Minute-Interview-Preparation.md)** (7 min): Read the timed script: 30s self-intro, 60s pitch, 2-minute architectural explanation, and closing statement.
3. **[01-Project-Overview.md](01-Project-Overview.md)** (3 min): Re-read Section 6 for the 30-second and 60-second elevator pitches.

---

### Plan B: "Core Technical Preparation" (1 to 2 Hours Available)
If you have 1 to 2 hours to prepare, follow this structured 6-step study pathway:
1. **[01-Project-Overview.md](01-Project-Overview.md)**: Master the logistics business problem, carrier differences, and business outcomes.
2. **[02-API-Led-Architecture.md](02-API-Led-Architecture.md)**: Understand the logical Experience, Process, and System layers implemented in the single Mule application.
3. **[07-Flow-Execution-Order.md](07-Flow-Execution-Order.md)**: Trace how a request flows from HTTP ingress $\rightarrow$ authentication $\rightarrow$ normalization $\rightarrow$ idempotency $\rightarrow$ risk engine $\rightarrow$ database $\rightarrow$ notification queue.
4. **[10-DataWeave-and-Carrier-Mappings.md](10-DataWeave-and-Carrier-Mappings.md)**: Review how BlueDart and Delhivery schemas are normalized into the canonical event model.
5. **[11-Database-Tables-and-SQL.md](11-Database-Tables-and-SQL.md)**: Understand the 5 MySQL tables and how idempotency is enforced via `event_key` unique constraints.
6. **[23-Team-Contribution-and-Evaluator-Questions.md](23-Team-Contribution-and-Evaluator-Questions.md)**: Practice the top 35 evaluator questions and model answers.

---

### Plan C: "Comprehensive Deep Dive" (Full Preparation / Architect Mastery)
Read all documents in numerical order from `00` to `29`. This gives you comprehensive mastery over every processor, DataWeave line, connector timeout, and MUnit mock in the system.

---

## 4. Key Documents by Evaluator Focus Area

Evaluators often have specific specializations. Match your preparation to their questions:

| Evaluator Focus Area | Priority Documents to Read | Key Technical Topics |
|---|---|---|
| **Architecture & System Design** | [02-API-Led-Architecture.md](02-API-Led-Architecture.md)<br>[22-Technical-Decisions-and-Tradeoffs.md](22-Technical-Decisions-and-Tradeoffs.md) | Logical API-led layering, decoupled messaging, outbox pattern, single-app vs. multi-app trade-offs. |
| **Mule 4 Implementation & Code** | [07-Flow-Execution-Order.md](07-Flow-Execution-Order.md)<br>[08-Flow-by-Flow-Explanation.md](08-Flow-by-Flow-Explanation.md)<br>[09-Connector-Reference.md](09-Connector-Reference.md) | Flow processors, variables, subflow reusability, VM connectors, APIKit routing. |
| **Data Transformation & DWL** | [10-DataWeave-and-Carrier-Mappings.md](10-DataWeave-and-Carrier-Mappings.md) | Canonical model design, timezone normalization (+05:30 to UTC), fallback dictionaries. |
| **Data Persistence & ACID** | [11-Database-Tables-and-SQL.md](11-Database-Tables-and-SQL.md) | MySQL schema, `event_key` constraint, master state progression, quarantine buffer. |
| **Testing & Quality Assurance** | [15-MUnit-Tests-Explained.md](15-MUnit-Tests-Explained.md)<br>[16-Postman-and-Manual-Testing.md](16-Postman-and-Manual-Testing.md) | 9 automated MUnit test suites, mocking DB & VM, Postman test catalog. |
| **Security & Operational Resilience** | [13-Authentication-and-Security.md](13-Authentication-and-Security.md)<br>[14-Error-Handling-and-Retry.md](14-Error-Handling-and-Retry.md)<br>[17-Negative-Scenarios-and-Recovery.md](17-Negative-Scenarios-and-Recovery.md) | Webhook token validation, duplicate suppression, anti-regression, quarantine auto-reconciliation. |

---

## 5. How to Rehearse Answers Effectively

When answering technical questions during the evaluation, follow the **4-Part Answer Framework**:

1. **Direct Answer (5–10 seconds)**: Give a clear, direct answer to the question immediately.
2. **Project Code Context (10–15 seconds)**: Reference the specific file, flow, or component where it is implemented in this project.
3. **Technical Rationale (10–15 seconds)**: Explain *why* it was designed that way (business protection, idempotency, performance).
4. **Resilience / Edge Case (optional 10 seconds)**: Mention how failure or exceptions are handled gracefully.

### Example Rehearsal:
> **Evaluator**: *"How do you prevent duplicate webhook events from corrupting your shipment state?"*  
> **Your Response**:  
> *"We enforce duplicate prevention at two distinct layers. In the Process layer (`shipment-processing.xml`), every incoming event generates a deterministic `eventKey` based on carrier, tracking number, status, and scan timestamp. First, the application executes `subflow-check-duplicate-event` to query `shipment_tracking_events`. If a match is found, processing immediately halts, returning a `200 OK` with status `DUPLICATE_ACKNOWLEDGED`, skipping state mutation and notifications. Second, at the database layer, the `event_key` column is guarded by a strict `UNIQUE KEY` constraint, guaranteeing ACID-compliant deduplication even under high-concurrency race conditions."*

---

## 6. Verification Checklist Before Starting

Before walking into the evaluation room or sharing your screen:
- [ ] MySQL database `shipment_control_tower` is running and seeded using `database/sample-data.sql`.
- [ ] The MuleSoft application builds cleanly and deploys in Anypoint Studio on port `8081`.
- [ ] Postman is open with collection `Shipment-Tracking.postman_collection.json` and environment `local-environment.postman_environment.json`.
- [ ] Anypoint Studio Console view is visible and cleared, ready to show structured logging.
- [ ] You have reviewed [28-Quick-Revision-Cheat-Sheet.md](28-Quick-Revision-Cheat-Sheet.md).
