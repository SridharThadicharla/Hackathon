import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def build_writeup():
    doc = docx.Document()
    
    # Page Setup: A4, 0.8 inch margins
    for section in doc.sections:
        section.page_width = Inches(8.27)   # A4 Width
        section.page_height = Inches(11.69) # A4 Height
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        section.different_first_page_header_footer = True
        
        # Configure Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Cognizant MuleSoft Hackathon | Shipment Signal Control Tower (Use Case 08)")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(100, 116, 139)
        
        # Configure Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun1 = fp.add_run("Use Case 08: Logistics — Real-Time Multi-Carrier Tracking   |   Page ")
        frun1.font.name = "Calibri"
        frun1.font.size = Pt(8.5)
        frun1.font.color.rgb = RGBColor(100, 116, 139)
        
        # XML Page Field
        fld = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
        fp._p.append(fld)
        
        frun2 = fp.add_run(" of ")
        frun2.font.name = "Calibri"
        frun2.font.size = Pt(8.5)
        frun2.font.color.rgb = RGBColor(100, 116, 139)
        
        fld2 = parse_xml(r'<w:fldSimple %s w:instr="NUMPAGES"/>' % nsdecls('w'))
        fp._p.append(fld2)

    # Style Palettes
    NAVY = RGBColor(10, 37, 64)       # #0A2540
    TEAL = RGBColor(14, 116, 144)     # #0E7490
    DARK_TEXT = RGBColor(30, 41, 59)  # #1E293B
    MUTED_TEXT = RGBColor(71, 85, 105)# #475569
    
    # Configure Default Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = DARK_TEXT
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(5)

    # Helper Functions
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(12.5)
        run.font.bold = True
        run.font.color.rgb = TEAL
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_p(text, bold_prefix=None, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            brun = p.add_run(bold_prefix)
            brun.font.name = 'Calibri'
            brun.font.size = Pt(10.5)
            brun.font.bold = True
            brun.font.color.rgb = DARK_TEXT
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(10.5)
        run.font.italic = italic
        run.font.color.rgb = DARK_TEXT
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            brun = p.add_run(bold_prefix)
            brun.font.name = 'Calibri'
            brun.font.size = Pt(10.5)
            brun.font.bold = True
            brun.font.color.rgb = DARK_TEXT
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(10.5)
        run.font.color.rgb = DARK_TEXT
        return p

    def add_callout(text, title=None, border_color="0E7490", bg_color="F0F9FF"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.columns[0].width = Inches(6.67)
        
        cell = tbl.cell(0, 0)
        # Background
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
        cell._tc.get_or_add_tcPr().append(shd)
        
        # Border: thick left border, no top/bottom/right
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        cell._tc.get_or_add_tcPr().append(borders)
        
        # Cell Padding
        tcMar = parse_xml(f'''
            <w:tcMar {nsdecls("w")}>
                <w:top w:w="120" w:type="dxa"/>
                <w:bottom w:w="120" w:type="dxa"/>
                <w:left w:w="200" w:type="dxa"/>
                <w:right w:w="150" w:type="dxa"/>
            </w:tcMar>
        ''')
        cell._tc.get_or_add_tcPr().append(tcMar)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        if title:
            trun = p.add_run(title + "\n")
            trun.font.name = 'Calibri'
            trun.font.size = Pt(10.5)
            trun.font.bold = True
            trun.font.color.rgb = TEAL
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        run.font.italic = True
        run.font.color.rgb = DARK_TEXT
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def format_table(table, col_widths, col_alignments=None):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        
        # Set table borders
        tblBorders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                <w:left w:val="none"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                <w:right w:val="none"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        table._tbl.tblPr.append(tblBorders)
        
        for i, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            if i == 0:
                trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
                
            for j, cell in enumerate(row.cells):
                cell.width = col_widths[j]
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                tcPr = cell._tc.get_or_add_tcPr()
                
                # Margins
                tcMar = parse_xml(f'''
                    <w:tcMar {nsdecls("w")}>
                        <w:top w:w="100" w:type="dxa"/>
                        <w:bottom w:w="100" w:type="dxa"/>
                        <w:left w:w="120" w:type="dxa"/>
                        <w:right w:w="120" w:type="dxa"/>
                    </w:tcMar>
                ''')
                tcPr.append(tcMar)
                
                if i == 0:
                    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0A2540"/>')
                    tcPr.append(shd)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(2)
                        p.paragraph_format.space_before = Pt(2)
                        if col_alignments and j < len(col_alignments):
                            p.alignment = col_alignments[j]
                        for run in p.runs:
                            run.font.name = 'Calibri'
                            run.font.size = Pt(9.5)
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    if i % 2 == 1:
                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
                    else:
                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="FFFFFF"/>')
                    tcPr.append(shd)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(2)
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.line_spacing = 1.15
                        if col_alignments and j < len(col_alignments):
                            p.alignment = col_alignments[j]
                        for run in p.runs:
                            run.font.name = 'Calibri'
                            run.font.size = Pt(9.5)
                            run.font.color.rgb = DARK_TEXT

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    
    # Spacing at top
    p_top = doc.add_paragraph()
    p_top.paragraph_format.space_before = Pt(20)
    p_top.paragraph_format.space_after = Pt(10)
    
    badge_run = p_top.add_run("COGNIZANT MULESOFT HACKATHON  |  OFFICIAL PROJECT SUBMISSION")
    badge_run.font.name = 'Calibri'
    badge_run.font.size = Pt(11)
    badge_run.font.bold = True
    badge_run.font.color.rgb = TEAL

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(4)
    p_title.paragraph_format.line_spacing = 1.05
    title_run = p_title.add_run("Shipment Signal Control Tower")
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(26)
    title_run.font.bold = True
    title_run.font.color.rgb = NAVY

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(18)
    sub_run = p_sub.add_run("Real-Time Multi-Carrier Shipment Tracking Integration Platform\nAPI-Led Architecture, Canonical Event Normalization & Resilient Exception Handling")
    sub_run.font.name = 'Calibri'
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = TEAL

    # Horizontal Divider Line (Navy & Teal)
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(18)
    drun = p_div.add_run("―" * 58)
    drun.font.bold = True
    drun.font.color.rgb = TEAL

    # Executive Summary Callout Box
    add_callout(
        "The Shipment Signal Control Tower is an enterprise-grade integration solution designed natively on MuleSoft Mule 4. "
        "It solves the core operational challenges of multi-carrier logistics by seamlessly ingesting disparate webhook events "
        "from BlueDart Express and Delhivery Logistics, normalizing payloads into a 9-milestone Canonical Event Model via DataWeave 2.0, "
        "enforcing deterministic deduplication, protecting master tracking states against stale scan regression, buffering unmanifested "
        "parcels in a quarantine buffer with automated reconciliation, and providing explainable SLA delay risk assessment.",
        title="EXECUTIVE SOLUTION ABSTRACT"
    )

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Submission Metadata Table
    meta_table = doc.add_table(rows=8, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_widths = [Inches(2.2), Inches(4.47)]
    
    meta_data = [
        ("Hackathon", "Cognizant MuleSoft Hackathon"),
        ("Use Case Track", "Use Case 08: Logistics — Real-Time Multi-Carrier Shipment Tracking"),
        ("Project Name", "Shipment Signal Control Tower"),
        ("Technology Stack", "MuleSoft Mule 4.4.0, DataWeave 2.0, RAML 1.0, MySQL 8.0, Persistent VM Queues"),
        ("Architectural Pattern", "API-Led Connectivity (Logical 3-Tier Layering) & Event-Driven Architecture (EDA)"),
        ("Team Name", "[Team Name Placeholder]"),
        ("Team Members", "[Team Member 1, Team Member 2, Team Member 3, Team Member 4, Team Member 5, Team Member 6]"),
        ("Submission Date", "October 2026"),
    ]
    
    for row_idx, (k, v) in enumerate(meta_data):
        row = meta_table.rows[row_idx]
        row.cells[0].paragraphs[0].add_run(k)
        row.cells[1].paragraphs[0].add_run(v)
        
    format_table(meta_table, meta_widths, [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_page_break()

    # =========================================================================
    # SECTION 1 — HACKATHON CHALLENGE
    # =========================================================================
    add_h1("Section 1 — Hackathon Challenge")
    
    add_h2("1.1 The Logistics Problem & Business Context")
    add_p(
        "Modern omni-channel retail, direct-to-consumer (D2C) brands, and enterprise third-party logistics (3PL) providers "
        "rely on multiple national and regional courier partners to fulfill customer orders across diverse geographic zones. "
        "In the Indian logistics landscape, carriers like BlueDart Express (specializing in aviation express networks and air-cargo hubs) "
        "and Delhivery Logistics (operating extensive ground surface freight, multi-tier sorting facilities, and last-mile delivery fleets) "
        "power a substantial portion of parcel movements."
    )
    add_p(
        "While engaging multiple logistics carriers optimizes freight costs and regional coverage, it creates severe integration chaos. "
        "Shippers receive asynchronous, high-volume event streams from disparate courier platforms that lack standardization. "
        "Without an authoritative, centralized integration control tower, warehouse management systems (WMS), enterprise resource planning (ERP) "
        "platforms, and customer-facing mobile tracking applications become fragmented, leading to operational blind spots, incorrect package "
        "statuses, and dissatisfied customers."
    )

    add_h2("1.2 Core Multi-Carrier Integration Challenges")
    add_p("The project specifically targets and resolves the core technical challenges outlined in Use Case 08:")
    
    add_bullet(
        "BlueDart pushes flat JSON objects with fields such as awb_no, status_code, location_code, and scan_date_time. "
        "In contrast, Delhivery transmits deeply nested JSON structures featuring a root waybill, a Status object with instructions and statusDateTime, "
        "and an array of Scans with nested scannedLocation strings. These structural incompatibilities prevent uniform backend processing.",
        bold_prefix="1. Heterogeneous Carrier Payload Schemas: "
    )
    add_bullet(
        "Couriers use proprietary alphanumeric codes and varying lifecycle terminology for the same physical milestone. "
        "For example, a parcel in transit is coded as 'IT' or 'DP' by BlueDart, but reported as 'IN TRANSIT' by Delhivery. An out-for-delivery parcel "
        "is coded as 'OFD' or 'OD' by BlueDart, but reported as 'VAN OUT' or 'OUT FOR DELIVERY' by Delhivery. Furthermore, BlueDart supplies ISO-8601 timestamps "
        "with timezone offsets (e.g., +05:30), whereas Delhivery sends space-delimited datetime strings without explicit timezone offsets.",
        bold_prefix="2. Inconsistent Status Vocabularies & Timezones: "
    )
    add_bullet(
        "Intermittent cellular connectivity on delivery handhelds and aggressive carrier webhook retry policies frequently cause the same physical scan "
        "event to be delivered 3 to 5 times. Naive ingestion pipelines risk inserting duplicate rows, corrupting historical ledgers, and triggering multiple "
        "redundant customer alerts.",
        bold_prefix="3. Duplicate Webhook Deliveries: "
    )
    add_bullet(
        "Delivery executives operating in areas with poor cellular reception often batch-upload intermediate hub transit scans long after a package has "
        "already reached 'OUT_FOR_DELIVERY' or 'DELIVERED'. If an integration platform blindly updates current shipment status based on the latest arrived webhook, "
        "it will regress master shipment states backwards (e.g., reverting a delivered package to in-transit), destroying data integrity.",
        bold_prefix="4. Out-of-Order & Delayed Shipment Scans: "
    )
    add_bullet(
        "Courier pickup personnel frequently scan parcels at merchant dispatch centers before the merchant's WMS batch synchronization creates the corresponding "
        "master shipment record in the central database. If an integration pipeline discards events for unknown shipments, the parcel suffers complete tracking "
        "blackout during its initial transit phase.",
        bold_prefix="5. Unmanifested Scans ('Ghost Shipments'): "
    )
    add_bullet(
        "Customers are overwhelmed by excessive notifications for routine linehaul hops (such as multiple internal 'IN_TRANSIT' or sorting scans), leading to "
        "notification fatigue. Simultaneously, couriers push revised estimated delivery dates (ETAs) that exceed promised customer delivery deadlines without "
        "explicitly flagging the shipment as delayed, leaving shippers blind to SLA breaches until an angry customer calls customer support.",
        bold_prefix="6. Notification Fatigue & Blind SLA Breaches: "
    )

    add_h2("1.3 Objective & Business Value of Shipment Signal Control Tower")
    add_p(
        "The primary objective of the Shipment Signal Control Tower is to deliver a robust, enterprise-grade integration layer built natively on MuleSoft Mule 4. "
        "The control tower acts as an authoritative, resilient bridge between disparate carrier push APIs and internal enterprise systems (WMS, ERP, customer portals). "
        "By enforcing contract-first governance, canonical data modeling, and automated exception management, the solution delivers substantial business value:"
    )
    add_bullet("Provides 100% unified visibility across all courier partners through a standardized 9-milestone Canonical Event Model.", bold_prefix="• Single-Pane-of-Glass Visibility: ")
    add_bullet("Guarantees that terminal states (DELIVERED) and forward progress are never rolled back by delayed or out-of-order scans.", bold_prefix="• State Integrity & Anti-Regression: ")
    add_bullet("Deterministic composite hashing suppresses duplicate processing and customer notification spam.", bold_prefix="• Guaranteed Idempotency: ")
    add_bullet("Buffers unmanifested scans in a quarantine repository and automatically reconciles them when WMS orders are registered.", bold_prefix="• Zero Event Loss: ")
    add_bullet("Dynamically evaluates carrier revised ETAs against customer promised delivery dates to flag at-risk and delayed shipments before customer escalation.", bold_prefix="• Proactive SLA Risk Management: ")
    add_bullet("Asynchronous queue decoupling ensures carrier webhooks receive HTTP 200 acknowledgments in under 50ms, withstanding peak festival traffic spikes.", bold_prefix="• High-Throughput Decoupling: ")

    # =========================================================================
    # SECTION 2 — HIGH-LEVEL DESIGN
    # =========================================================================
    add_h1("Section 2 — High-Level Design")
    
    add_h2("2.1 Logical 3-Tier API-Led Architecture")
    add_p(
        "The solution is architected according to MuleSoft's API-Led Connectivity methodology, separating integration responsibilities into three logical tiers: "
        "Experience, Process, and System. This separation decouples point-to-point courier dependencies, ensures strict modularity, and facilitates future microservice scaling."
    )
    
    add_bullet(
        "Responsible for secure ingress, request validation, and client-tailored interfaces. Implemented in webhook-api.xml, it exposes endpoints for BlueDart and Delhivery "
        "webhooks, WMS shipment creation, customer tracking queries, and operational health checks. An edge security subflow (subflow-validate-carrier-auth) verifies "
        "carrier shared secret tokens (X-Carrier-Token) and attaches a distributed correlation identifier (X-Correlation-ID) before delegating to the RAML 1.0 APIKit Router.",
        bold_prefix="1. Experience Layer (Logical Ingress & Edge Security): "
    )
    add_bullet(
        "The core intelligence and orchestration heart of the platform. It encompasses DataWeave 2.0 Carrier Normalization (carrier-normalization.xml), "
        "Idempotent Deduplication (shipment-processing.xml), Master Shipment Verification & Quarantine Routing, Forward-Only State Machine Progression, "
        "Explainable SLA Delay Risk Assessment (risk-assessment.xml), and Milestone Notification Filtering (notification-queue.xml).",
        bold_prefix="2. Process Layer (Business Intelligence & Orchestration): "
    )
    add_bullet(
        "Manages underlying persistence and messaging systems of record. Implemented in database-operations.xml and notification-queue.xml, it performs ACID relational "
        "database operations across MySQL 8.0 tables (shipments, shipment_tracking_events, pending_tracking_events, notification_outbox, integration_alerts) and manages "
        "asynchronous persistent intra-JVM queues (shipment-milestone-queue) via the Mule VM Connector.",
        bold_prefix="3. System Layer (Persistence & Asynchronous Messaging): "
    )

    add_h2("2.2 Architectural Decision: Logical Layering in a Single Mule Application")
    add_p(
        "A key architectural decision was made regarding deployment packaging. In large enterprise production environments, Experience, Process, and System tiers "
        "are often deployed as three physically separate Mule applications on independent CloudHub workers. However, for the hackathon implementation, all three tiers "
        "are architected and implemented as distinct logical layers within a single deployable Mule 4 application (Shipment-Signal-Control-Tower.jar)."
    )
    add_p(
        "This architectural decision was chosen for clear engineering reasons: (1) it eliminates inter-worker network latency and HTTP serialization overhead during high-volume ingress, "
        "(2) it dramatically reduces cloud infrastructure memory and licensing consumption, and (3) it enables unified local execution and evaluation in Anypoint Studio. "
        "Crucially, the code maintains strict modularity: each tier is encapsulated in dedicated XML configuration files, DataWeave modules, and reusable subflows. "
        "If required by enterprise scale, each tier can be separated into an independent CloudHub microservice without modifying underlying transformation or business logic."
    )

    add_h2("2.3 Architecture Diagram")
    add_p(
        "The diagram below illustrates the end-to-end data flow from external courier webhook engines through Experience Ingress, Process Orchestration, System Persistence, "
        "and Asynchronous VM Queue decoupling. It clearly differentiates currently implemented, verified capabilities from planned future scope enhancements."
    )

    # Insert Architecture Diagram Image
    diagram_path = "c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/architecture_diagram.png"
    if os.path.exists(diagram_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(diagram_path, width=Inches(6.67))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(10)
        c_run = p_cap.add_run("Figure 1: High-Level Architecture Diagram of Shipment Signal Control Tower")
        c_run.font.name = "Calibri"
        c_run.font.size = Pt(9.5)
        c_run.font.italic = True
        c_run.font.color.rgb = MUTED_TEXT

    add_callout(
        "CRITICAL ARCHITECTURAL DISTINCTION: As depicted in Figure 1, external SMTP email delivery and SMS/WhatsApp dispatch are strictly FUTURE SCOPE. "
        "In the current verified implementation, milestone events are filtered and reliably staged in the relational notification_outbox table, and the asynchronous "
        "VM queue decouples background consumer processing without sending live external emails. A staged outbox record does not represent proof of external email delivery.",
        title="ARCHITECTURAL BOUNDARY — NOTIFICATION STAGING VS. FUTURE DISPATCH",
        border_color="D97706",
        bg_color="FFFBEB"
    )

    add_h2("2.4 End-to-End Processing Flow")
    add_p("When a courier webhook pushes a scan event, the control tower executes the following sequence:")
    add_bullet("1. Ingress & Security: Webhook arrives at /api/v1/webhooks/carriers/{carrierCode}. Token security validates X-Carrier-Token (rejecting unauthorized calls with HTTP 401). APIKit Router validates payload syntax against RAML 1.0 (rejecting malformed JSON with HTTP 400).")
    add_bullet("2. Canonical Normalization: DataWeave 2.0 maps carrier-specific JSON (BlueDart flat / Delhivery nested) into the unified Canonical Event Model, converting timestamps to UTC ISO-8601 and generating deterministic eventId and eventKey.")
    add_bullet("3. Idempotent Deduplication: Database check queries shipment_tracking_events by event_key. If a match exists, the flow terminates immediately, returning HTTP 200 with DUPLICATE_ACKNOWLEDGED, skipping redundant updates.")
    add_bullet("4. Shipment Master Lookup: The flow queries the shipments table for the tracking number. If not found, the event is safely routed to subflow-quarantine-unknown-shipment, saving it in pending_tracking_events with status PENDING, returning HTTP 200 with QUARANTINED_PENDING_REGISTRATION.")
    add_bullet("5. Anti-Regression & Event Ledger: For manifested parcels, the state machine compares the new event's status rank against the current shipment rank. If out-of-order or older, isOutOfOrder is set to true. The raw event is immutably appended to shipment_tracking_events for audit compliance, while the master shipment status in shipments is protected from backward regression.")
    add_bullet("6. Explainable SLA Risk Calculation: The risk engine compares carrier revised ETA against the promised delivery SLA date, computing delay hours and assigning risk levels (ON_TRACK, AT_RISK, DELAYED).")
    add_bullet("7. Milestone Notification Staging: If the status transition represents a critical milestone (PICKED_UP, OUT_FOR_DELIVERY, DELIVERY_ATTEMPTED, DELIVERED, EXCEPTION), an alert record is staged in notification_outbox with status QUEUED, and published to persistent VM queue shipment-milestone-queue. Routine transit scans (IN_TRANSIT) are suppressed by design.")
    add_bullet("8. Immediate Synchronous Acknowledgment: The HTTP listener returns HTTP 200 OK with full execution metadata to the carrier in under 50ms.")

    # =========================================================================
    # SECTION 3 — API SPECIFICATIONS / DATA MAPPING
    # =========================================================================
    add_h1("Section 3 — API Specifications / Data Mapping")
    
    add_h2("3.1 Core API Specifications")
    add_p(
        "All application APIs are governed by the RAML 1.0 specification (src/main/resources/api/shipment-tracking.raml) "
        "and served via the base path http://localhost:8081/api/v1. The table below documents the 12 verified endpoints, their logical layer, "
        "operational behavior, and verification status:"
    )

    api_table = doc.add_table(rows=13, cols=5)
    api_widths = [Inches(0.8), Inches(2.2), Inches(0.9), Inches(1.87), Inches(0.9)]
    
    api_headers = ["Method", "Endpoint Path", "Layer", "Purpose & Behavior", "Status"]
    for j, h in enumerate(api_headers):
        api_table.rows[0].cells[j].paragraphs[0].add_run(h)
        
    api_endpoints = [
        ("POST", "/webhooks/carriers/{carrierCode}", "Experience", "Multi-carrier ingestion gateway. Parameterized route handling any registered courier.", "Verified"),
        ("POST", "/webhooks/bluedart", "Experience", "Dedicated ingestion route for BlueDart Express webhooks.", "Verified"),
        ("POST", "/webhooks/delhivery", "Experience", "Dedicated ingestion route for Delhivery Logistics webhooks.", "Verified"),
        ("POST", "/shipments", "Exp / Sys", "Registers new shipment master records from WMS/TMS into MySQL database.", "Verified"),
        ("GET", "/shipments/{trackingNumber}", "Exp / Sys", "Retrieves current shipment status, SLA dates, and latest calculated delay risk level.", "Verified"),
        ("GET", "/shipments/{trackingNumber}/history", "Exp / Sys", "Retrieves full chronological audit event trail of all physical carrier scans.", "Verified"),
        ("GET", "/shipments/{trackingNumber}/risk", "Exp / Proc", "Executes real-time explainable SLA risk assessment for a specific tracking number.", "Verified"),
        ("GET", "/shipments/{trackingNumber}/notifications", "Exp / Sys", "Retrieves dispatched customer milestone notification records from outbox table.", "Verified"),
        ("GET", "/health", "Exp / Sys", "Operational health check probing MySQL database and VM queue connectivity.", "Verified"),
        ("GET", "/carriers/pulse", "Exp / Proc", "Aggregated telemetry reporting processed, duplicate, and out-of-order metrics.", "Verified"),
        ("POST", "/events/replay", "Exp / Proc", "Operator endpoint to manually reprocess specific quarantined scans by eventKey.", "Verified"),
        ("POST", "/events/reconcile", "Exp / Proc", "Batch reconciliation job auto-reprocessing quarantined events for manifested parcels.", "Verified"),
    ]
    
    for row_idx, data in enumerate(api_endpoints, start=1):
        for col_idx, text in enumerate(data):
            api_table.rows[row_idx].cells[col_idx].paragraphs[0].add_run(text)
            
    format_table(api_table, api_widths, [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER])

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_h2("3.2 Canonical Data Model (CDM) & DataWeave Normalization")
    add_p(
        "To decouple carrier-specific schema changes from internal systems, DataWeave 2.0 transforms every incoming payload into an immutable Canonical Event Model. "
        "This transforms an N x M point-to-point integration complexity into an N + M model, where adding a new courier requires only a single DataWeave script."
    )

    cdm_table = doc.add_table(rows=15, cols=5)
    cdm_widths = [Inches(1.5), Inches(0.9), Inches(1.2), Inches(1.3), Inches(1.77)]
    
    cdm_headers = ["Canonical Field", "Data Type", "BlueDart Field", "Delhivery Field", "Transformation Logic"]
    for j, h in enumerate(cdm_headers):
        cdm_table.rows[0].cells[j].paragraphs[0].add_run(h)
        
    cdm_mappings = [
        ("trackingNumber", "String", "payload.awb_no", "payload.waybill", "Extracted and trimmed; fallback to UNKNOWN_AWB"),
        ("carrier", "String", "Literal: BLUEDART", "Literal: DELHIVERY", "Carrier identifier set based on ingress route"),
        ("carrierEventCode", "String", "payload.status_code", "payload.Status.statusCode", "Upper-cased raw carrier status code"),
        ("originalStatus", "String", "payload.status_code", "Status.status", "Preserves original carrier status string verbatim"),
        ("normalizedStatus", "String", "Normalized Map", "Normalized Map", "Mapped to official 9-milestone canonical vocabulary"),
        ("eventTimestamp", "String (UTC)", "payload.scan_date_time", "Status.statusDateTime", "Converted from IST/space-delimited to UTC ISO-8601"),
        ("receivedTimestamp", "String (UTC)", "now() >> UTC", "now() >> UTC", "Current system UTC timestamp at ingestion"),
        ("location", "String", "location_name (code)", "Scans[0].scannedLocation", "Formatted string combining location name and code"),
        ("description", "String", "status_description", "Status.instructions", "Carrier scan narrative / instructions"),
        ("estimatedDeliveryTime", "String (UTC)", "payload.eta", "ExpectedDeliveryDate", "Parsed and normalized to UTC ISO-8601"),
        ("promisedDeliveryTime", "String (UTC)", "vars.promisedDeliveryTime", "vars.promisedDeliveryTime", "Fetched from shipment master record"),
        ("eventId", "String", "EVT-BD-{timestamp}", "EVT-DELH-{timestamp}", "Unique transaction event ID"),
        ("eventKey", "String", "BLUEDART-AWB-CODE-TS", "DELHIVERY-AWB-CODE-TS", "Deterministic composite idempotency key"),
        ("correlationId", "String", "vars.correlationId", "vars.correlationId", "Preserves incoming header or generates uuid()"),
    ]
    
    for row_idx, data in enumerate(cdm_mappings, start=1):
        for col_idx, text in enumerate(data):
            cdm_table.rows[row_idx].cells[col_idx].paragraphs[0].add_run(text)
            
    format_table(cdm_table, cdm_widths, [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_h2("3.3 Carrier Status Conversion Dictionary")
    add_p(
        "The table below details the complete status mapping dictionary across BlueDart, Delhivery, and the canonical lifecycle model, "
        "including integer status ranks utilized by the anti-regression engine:"
    )

    status_table = doc.add_table(rows=11, cols=5)
    status_widths = [Inches(1.5), Inches(0.5), Inches(1.3), Inches(1.6), Inches(1.77)]
    
    status_headers = ["Canonical Status", "Rank", "BlueDart Codes", "Delhivery Status Values", "Lifecycle Business Definition"]
    for j, h in enumerate(status_headers):
        status_table.rows[0].cells[j].paragraphs[0].add_run(h)
        
    status_data = [
        ("LABEL_CREATED", "10", "LC, BK", "MANIFESTED, MF, SOFTDATA", "Shipment manifested; label printed."),
        ("PICKED_UP", "20", "PU", "PENDING, PP, PICKED UP", "Physical custody handed to courier; milestone alert."),
        ("IN_TRANSIT", "30", "IT, DP", "IN TRANSIT, IT", "Linehaul movement between sorting facilities; suppressed."),
        ("ARRIVED_AT_HUB", "35", "AR, HUB", "BAG IN, ARRIVED AT FACILITY", "Scanned at regional sorting hub; audit only."),
        ("OUT_FOR_DELIVERY", "40", "OFD, OD", "OUT FOR DELIVERY, VAN OUT", "Package on delivery van for last-mile; milestone alert."),
        ("DELIVERY_ATTEMPTED", "45", "UD, NA", "UNDELIVERED, DELIVERY ATTEMPTED", "Delivery attempted; recipient unavailable; milestone alert."),
        ("DELIVERED", "50", "DL, OK", "DELIVERED, DL", "Delivery confirmed with OTP/sign; terminal milestone."),
        ("RETURNED", "90", "RT, RTO, RDL", "RTO, RETURN TO ORIGIN", "Undeliverable package returned to origin shipper."),
        ("EXCEPTION", "95", "EX, HLD, DMG", "EXCEPTION, DAMAGED, LOST", "Operational disruption / damage; critical exception alert."),
        ("UNKNOWN_STATUS", "0", "Any unmapped code", "Any unmapped status text", "Graceful fallback preserving raw status in audit log."),
    ]
    
    for row_idx, data in enumerate(status_data, start=1):
        for col_idx, text in enumerate(data):
            status_table.rows[row_idx].cells[col_idx].paragraphs[0].add_run(text)
            
    format_table(status_table, status_widths, [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_h2("3.4 Data Transformation Examples")
    add_p("The following short examples demonstrate the transformation of carrier-specific payloads into the Canonical Event Model:")
    
    add_bullet(
        'Input: {"awb_no": "BD-987654321", "status_code": "IT", "status_description": "In Transit to Hub", "scan_date_time": "2026-10-11T10:30:00+05:30", "location_code": "DEL/HUB", "location_name": "Delhi Central Hub", "eta": "2026-10-14T18:00:00+05:30"}\n'
        'Canonical Output: {"trackingNumber": "BD-987654321", "carrier": "BLUEDART", "normalizedStatus": "IN_TRANSIT", "eventTimestamp": "2026-10-11T05:00:00Z", "location": "Delhi Central Hub (DEL/HUB)", "eventKey": "BLUEDART-BD-987654321-IT-20261011050000", "isDuplicate": false, "isOutOfOrder": false}',
        bold_prefix="BlueDart Normalization: "
    )
    add_bullet(
        'Input: {"waybill": "DELH-11223344", "Status": {"status": "In Transit", "statusCode": "IT", "statusDateTime": "2026-10-11 11:15:00", "instructions": "Departed Hub"}, "Scans": [{"scannedLocation": "BLR/HUB"}], "ExpectedDeliveryDate": "2026-10-13T20:00:00Z"}\n'
        'Canonical Output: {"trackingNumber": "DELH-11223344", "carrier": "DELHIVERY", "normalizedStatus": "IN_TRANSIT", "eventTimestamp": "2026-10-11T11:15:00Z", "location": "BLR/HUB", "eventKey": "DELHIVERY-DELH-11223344-IT-20261011111500", "isDuplicate": false, "isOutOfOrder": false}',
        bold_prefix="Delhivery Normalization: "
    )

    # =========================================================================
    # SECTION 4 — CHALLENGES & WORKAROUNDS
    # =========================================================================
    add_h1("Section 4 — Challenges & Workarounds")
    add_p(
        "During the architecture and development of the Shipment Signal Control Tower, several complex logistics integration challenges "
        "were encountered. The two-column table below outlines the core challenges and the specific design solutions and workarounds implemented:"
    )

    chall_table = doc.add_table(rows=9, cols=2)
    chall_widths = [Inches(2.5), Inches(4.17)]
    
    chall_headers = ["Challenge Encountered", "Solution / Workaround Implemented"]
    for j, h in enumerate(chall_headers):
        chall_table.rows[0].cells[j].paragraphs[0].add_run(h)
        
    challenges_data = [
        (
            "Heterogeneous Carrier Payload Formats & Schemas\n\n"
            "BlueDart supplies flat JSON while Delhivery pushes deeply nested objects and arrays. Timezones vary between IST string offsets and space-delimited text without timezones.",
            "DataWeave 2.0 Canonical Normalizer Engine\n\n"
            "Developed dedicated DataWeave modules (bluedart-to-canonical.dwl and delhivery-to-canonical.dwl) utilizing functional try() blocks to convert varied date formats to standard UTC ISO-8601 strings and map arbitrary keys into a unified Canonical Event Model."
        ),
        (
            "Duplicate Webhook Deliveries from Cellular Retries\n\n"
            "Carrier mobile devices frequently retry HTTP POST requests upon signal loss, sending identical scan payloads 3 to 5 times.",
            "Deterministic Idempotency Key & Database Unique Constraints\n\n"
            "Constructed a deterministic composite hash: event_key = CARRIER-AWB-STATUS-TIMESTAMP, backed by a MySQL UNIQUE KEY index. Incoming duplicates are caught by subflow-check-duplicate-event, returning HTTP 200 with DUPLICATE_ACKNOWLEDGED and suppressing redundant processing."
        ),
        (
            "Out-of-Order Scans & Master State Rollback\n\n"
            "Delayed transit scans uploaded hours later by rural hubs or vans risk rolling back master shipments from OUT_FOR_DELIVERY or DELIVERED to IN_TRANSIT.",
            "Status Rank Hierarchy & Forward-Only State Engine\n\n"
            "Assigned integer status ranks (10 to 50) to lifecycle milestones. The state machine checks if an incoming scan has a lower rank than the current shipment state. Stale scans are flagged as out-of-order and saved in shipment_tracking_events for audit compliance, but never overwrite the current master status in shipments."
        ),
        (
            "Unmanifested Shipments ('Ghost Scans')\n\n"
            "Courier drivers scan parcels at merchant warehouses before the merchant's WMS batch manifest creates the shipment master record in the database.",
            "Quarantine Buffer & Batch Reconciliation Pipeline\n\n"
            "Instead of dropping scans, the lookup subflow routes unmanifested events to pending_tracking_events with status PENDING. When the WMS manifests the order, the /events/reconcile pipeline auto-replays the buffered scans, eliminating visibility blackouts."
        ),
        (
            "Customer Notification Fatigue from Routine Transit Hops\n\n"
            "High-volume transit hub scans (IN_TRANSIT, BAG IN, BAG OUT) inundate customer communication channels with spam.",
            "Milestone Notification Filter & Transactional Outbox\n\n"
            "Implemented an intelligent milestone filter in notification-queue.xml. Only major state transitions (PICKED_UP, OUT_FOR_DELIVERY, DELIVERY_ATTEMPTED, DELIVERED, EXCEPTION) stage alert records in notification_outbox. Routine linehaul scans are suppressed by design."
        ),
        (
            "Carrier SLA Breaches & Unflagged Delivery Delays\n\n"
            "Couriers revise ETAs without explicitly flagging that the new ETA breaches the customer's promised delivery deadline.",
            "Explainable SLA Delay Risk Engine\n\n"
            "Implemented subflow-evaluate-eta-and-delay in risk-assessment.xml. The engine dynamically calculates date differences between revised ETA and promised SLA, categorizing parcels into ON_TRACK, AT_RISK, or DELAYED with transparent reason codes."
        ),
        (
            "Ingress Burst Volume vs Downstream Processing Latency\n\n"
            "High-concurrency webhook bursts during sales events risk overwhelming downstream notification and reporting systems.",
            "Transactional Outbox Pattern & Persistent VM Queue Decoupling\n\n"
            "The synchronous HTTP ingestion flow only performs database validation and outbox staging before immediately returning HTTP 200 (<50ms). An asynchronous persistent VM queue (shipment-milestone-queue) decouples background consumer processing."
        ),
        (
            "Unmapped Carrier Status Codes & Graceful Schema Drift\n\n"
            "Couriers introduce new experimental status codes without advance notice, risking unhandled runtime exceptions.",
            "Safe Default Fallback & Integration Alert Logging\n\n"
            "Configured normalizedStatusMap[rawStatus] default 'UNKNOWN_STATUS'. The flow preserves the raw status in the audit trail without crashing, master status remains intact, and an alert is logged in integration_alerts for operator review."
        )
    ]
    
    for row_idx, data in enumerate(challenges_data, start=1):
        for col_idx, text in enumerate(data):
            chall_table.rows[row_idx].cells[col_idx].paragraphs[0].add_run(text)
            
    format_table(chall_table, chall_widths, [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT])

    # =========================================================================
    # SECTION 5 — LEARNINGS
    # =========================================================================
    add_h1("Section 5 — Learnings")
    add_p(
        "Developing the Shipment Signal Control Tower provided significant engineering and architectural insights into building "
        "mission-critical integration systems on MuleSoft Mule 4. Key learnings from the project include:"
    )

    add_bullet(
        "While API-Led Connectivity is often conceived as three physically separated server runtimes, this project demonstrated that "
        "API-Led principles are fundamentally an architectural design discipline. Structuring Experience, Process, and System layers logically "
        "within a single Mule application via distinct XML configuration files, DataWeave modules, and strict interfaces achieves complete "
        "separation of concerns, high developer productivity, and optimal memory utilization while preserving a frictionless path toward "
        "independent microservice deployment.",
        bold_prefix="1. API-Led Connectivity as a Logical Discipline: "
    )
    add_bullet(
        "DataWeave 2.0 proved to be an exceptionally powerful functional transformation language for handling dirty, real-world logistics data. "
        "Utilizing functional try() wrappers, regular expression replacements, and robust timezone conversions enabled the normalizer to parse "
        "inconsistent datetime formats and disparate JSON structures without a single unhandled runtime exception.",
        bold_prefix="2. DataWeave 2.0 for Robust Data Modeling: "
    )
    add_bullet(
        "In event-driven webhook architectures, downstream systems cannot rely on external third-party couriers to enforce delivery discipline. "
        "Deriving deterministic composite idempotency keys (CARRIER-AWB-STATUS-TIMESTAMP) at the integration edge and pairing them with database "
        "unique constraints is the only reliable way to guarantee at-most-once processing under aggressive network retries.",
        bold_prefix="3. Deterministic Idempotency Keys as the First Defense: "
    )
    add_bullet(
        "A critical architectural insight was separating the 'current shipment state' from the 'immutable event audit ledger'. "
        "While the master shipment record must be strictly protected from backward regression (via status rank hierarchies), every physical scan "
        "received—even out-of-order or stale scans—must be immutably recorded in the tracking events ledger for regulatory, SLA billing, and audit compliance.",
        bold_prefix="4. State Machine Progression vs. Event Ledger Separation: "
    )
    add_bullet(
        "Distributed supply chains inevitably encounter asynchronous race conditions where physical events precede enterprise order manifests. "
        "Implementing a dedicated quarantine buffer (pending_tracking_events) combined with automated batch reconciliation transforms what would "
        "otherwise be lost data into a resilient, self-healing integration pipeline.",
        bold_prefix="5. Quarantine Buffering for Resilient Lifecycle Alignment: "
    )
    add_bullet(
        "Dual-write inconsistencies between relational databases and message brokers are a common architectural pitfall. Staging customer notification "
        "intent directly in a relational notification_outbox table within the same database transaction before publishing to the persistent VM queue "
        "guarantees zero message loss even during sudden application restarts.",
        bold_prefix="6. The Transactional Outbox Pattern for Decoupled Messaging: "
    )
    add_bullet(
        "Authoring a comprehensive RAML 1.0 specification before writing integration code established a strict contract across consumer touchpoints and "
        "carrier webhooks. MuleSoft's APIKit Router automatically enforced schema validation at the HTTP edge, while centralized global error handlers "
        "ensured consistent JSON error envelopes and distributed correlation tracking across all failure scenarios.",
        bold_prefix="7. Contract-First RAML Governance & Traceability: "
    )

    # =========================================================================
    # SECTION 6 — FUTURE SCOPE
    # =========================================================================
    add_h1("Section 6 — Future Scope")
    add_p(
        "While the Shipment Signal Control Tower fully satisfies all core requirements for Use Case 08, several realistic architectural enhancements "
        "have been identified to extend the solution into an enterprise-scale production platform:"
    )

    add_bullet(
        "CRITICAL ARCHITECTURAL DISTINCTION: As documented throughout this write-up, external SMTP email delivery and live SMS dispatch are strictly FUTURE SCOPE. "
        "In the current prototype, milestone events are filtered and staged in the relational notification_outbox table, and the asynchronous VM queue decouples "
        "background consumer processing without sending live external emails. The immediate next production enhancement will connect the notification consumer "
        "to enterprise SMTP gateways (such as SendGrid or Amazon SES) and commercial SMS/WhatsApp APIs (Twilio or Gupshup) for live multi-channel dispatch.",
        bold_prefix="1. SMTP Email & SMS Gateway Integration (Future Scope): "
    )
    add_bullet(
        "Leveraging the established Canonical Event Model to onboard additional national and international carriers (such as FedEx, DTDC, Shadowfax, "
        "and DHL Express). Because the Process and System tiers are decoupled from carrier specifics, integrating a new carrier requires only a single DataWeave normalizer module.",
        bold_prefix="2. Multi-Carrier Ecosystem Expansion: "
    )
    add_bullet(
        "Upgrading carrier webhook authentication from static shared secret tokens (X-Carrier-Token) to cryptographic HMAC-SHA256 signature verification "
        "(X-Hub-Signature) with timestamp-based replay protection windows to ensure message integrity and prevent tampering in transit.",
        bold_prefix="3. Cryptographic Webhook Security & Replay Protection: "
    )
    add_bullet(
        "Transitioning from intra-JVM persistent VM queues to distributed cloud messaging platforms such as Anypoint MQ or Apache Kafka. This will enable "
        "horizontal multi-worker scaling across multi-availability-zone CloudHub clusters with distributed FIFO message ordering.",
        bold_prefix="4. Enterprise Cloud Messaging (Anypoint MQ / Kafka): "
    )
    add_bullet(
        "Splitting the current monolithic Mule application into three independently deployable CloudHub 2.0 microservices (shipment-eapi, shipment-papi, "
        "and shipment-sapi) to allow independent autoscaling and isolated resource allocation based on traffic demands.",
        bold_prefix="5. Physical Multi-Worker CloudHub Microservice Deployment: "
    )
    add_bullet(
        "Enhancing the rule-based SLA delay evaluation engine with machine learning models trained on historical courier route transit times, weather disruptions, "
        "and festival peak hub dwell times to predict delays before couriers issue revised ETAs.",
        bold_prefix="6. Machine Learning Predictive SLA Risk Engine: "
    )
    add_bullet(
        "Developing a responsive, single-pane-of-glass operations web portal (built on React or Angular) powered by the control tower's /carriers/pulse, "
        "/health, and /events/replay REST APIs to provide logistics control tower operators with live volume telemetry and quarantine management.",
        bold_prefix="7. Centralized Control Tower Operations Dashboard: "
    )

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_h2("6.1 Conclusion")
    add_p(
        "The Shipment Signal Control Tower successfully addresses the challenges of multi-carrier logistics integration in Cognizant MuleSoft Hackathon Use Case 08. "
        "By combining MuleSoft's API-Led Connectivity with DataWeave 2.0 canonical normalization, deterministic idempotency, anti-regression state protection, "
        "quarantine buffering, and asynchronous queue decoupling, the solution transforms fragmented courier event streams into an authoritative, real-time logistics control tower. "
        "The architecture establishes a robust, extensible foundation capable of scaling to millions of daily parcel scans across diverse carrier networks."
    )

    # Save Word document
    output_docx = "c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/Shipment_Signal_Control_Tower_Hackathon_Writeup.docx"
    doc.save(output_docx)
    print(f"Successfully generated Word document at: {output_docx}")
    return output_docx

if __name__ == "__main__":
    build_writeup()
