import os
from PIL import Image, ImageDraw, ImageFont

def create_architecture_diagram(output_path):
    width = 1600
    height = 960
    
    # Create high-res canvas
    img = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_path_regular = "C:/Windows/Fonts/segoeui.ttf"
    font_path_bold = "C:/Windows/Fonts/segoeuib.ttf"
    font_path_semibold = "C:/Windows/Fonts/segoeuisl.ttf"
    
    title_font = ImageFont.truetype(font_path_bold, 28)
    subtitle_font = ImageFont.truetype(font_path_regular, 15)
    section_title_font = ImageFont.truetype(font_path_bold, 18)
    box_title_font = ImageFont.truetype(font_path_bold, 15)
    body_font = ImageFont.truetype(font_path_regular, 13)
    body_bold_font = ImageFont.truetype(font_path_bold, 13)
    badge_font = ImageFont.truetype(font_path_bold, 11)
    note_font = ImageFont.truetype(font_path_regular, 12)
    
    # Palette
    NAVY_DARK = "#0A2540"
    NAVY_MED = "#1E3A8A"
    TEAL_DARK = "#0E7490"
    TEAL_LIGHT = "#E0F2FE"
    GRAY_TEXT = "#334155"
    GRAY_MUTED = "#64748B"
    GRAY_BORDER = "#CBD5E1"
    GRAY_BG = "#FFFFFF"
    ACCENT_AMBER = "#D97706"
    ACCENT_AMBER_BG = "#FEF3C7"
    FUTURE_BG = "#FFFBEB"
    FUTURE_BORDER = "#D97706"
    
    # 1. Top Header Banner
    draw.rectangle([(0, 0), (width, 80)], fill=NAVY_DARK)
    draw.text((40, 15), "SHIPMENT SIGNAL CONTROL TOWER — HIGH-LEVEL ARCHITECTURE", fill="#FFFFFF", font=title_font)
    draw.text((40, 50), "API-Led Connectivity & Event-Driven Logistics Orchestration Engine | MuleSoft Mule 4.4.0", fill="#38BDF8", font=subtitle_font)
    
    # Draw Single App Container Outline
    # Box showing logical layering inside one Mule application
    draw.rounded_rectangle([(320, 100), (1240, 930)], radius=12, fill="#FFFFFF", outline=NAVY_MED, width=2)
    draw.text((340, 110), "SINGLE MULE APPLICATION RUNTIME BOUNDARY (Shipment-Signal-Control-Tower.jar)", fill=NAVY_MED, font=box_title_font)
    draw.text((340, 130), "Logical 3-tier layering maintained via distinct flow files, DataWeave modules, and ACID database operations", fill=GRAY_MUTED, font=note_font)

    # 2. Left Column: External Sources & Ingress Clients (X: 30 to 290)
    draw.rounded_rectangle([(30, 100), (290, 930)], radius=10, fill="#FFFFFF", outline=GRAY_BORDER, width=2)
    draw.rectangle([(30, 100), (290, 140)], fill="#F1F5F9")
    draw.text((45, 112), "EXTERNAL SOURCES & CLIENTS", fill=NAVY_DARK, font=section_title_font)
    
    sources = [
        ("BlueDart Express", "Carrier Webhook Ingress\nFlat JSON | AWB Number\nStatus: PU, IT, OFD, DL", 160, 260, "#0284C7"),
        ("Delhivery Logistics", "Carrier Webhook Ingress\nNested JSON | Waybill\nStatus: Manifested, Dispatched", 280, 380, "#0D9488"),
        ("WMS / ERP Systems", "Shipment Master Ingestion\nPOST /api/v1/shipments\nOrder Manifests & SLA Benchmarks", 400, 500, "#6366F1"),
        ("Customer Apps & Portals", "Tracking Consumers\nGET /shipments/{trackingNum}\nMaster Status & Chronological History", 520, 620, "#059669"),
        ("Control Tower Ops Console", "Operational Telemetry & Pulse\nGET /carriers/pulse\nGET /health | Reconcile & Replay", 640, 740, "#D97706"),
    ]
    
    for title, desc, y1, y2, color in sources:
        draw.rounded_rectangle([(45, y1), (275, y2)], radius=8, fill="#F8FAFC", outline=color, width=2)
        draw.text((55, y1 + 8), title, fill=NAVY_DARK, font=box_title_font)
        draw.text((55, y1 + 30), desc, fill=GRAY_TEXT, font=body_font)

    # 3. Layer 1: Experience Layer (X: 340 to 1220, Y: 160 to 290)
    draw.rounded_rectangle([(340, 160), (1220, 290)], radius=8, fill="#F0F9FF", outline=TEAL_DARK, width=2)
    draw.rectangle([(340, 160), (1220, 195)], fill=TEAL_DARK)
    draw.text((355, 168), "EXPERIENCE LAYER (Logical Ingress & Security Edge — webhook-api.xml)", fill="#FFFFFF", font=section_title_font)
    
    # Exp Layer Subcomponents
    exp_boxes = [
        ("HTTP Ingress Gateway", "HTTP Listener (:8081)\n/api/v1/* Base Path\nFast-Path REST Ingress", 360, 590),
        ("Token Security Gate", "subflow-validate-carrier-auth\nX-Carrier-Token Verification\nX-Correlation-ID Tracking", 610, 890),
        ("Contract & APIKit Router", "RAML 1.0 Strict Validation\nContract-First Auto-Routing\nImmediate 400 on Schema Drift", 910, 1200),
    ]
    for b_title, b_desc, bx1, bx2 in exp_boxes:
        draw.rounded_rectangle([(bx1, 205), (bx2, 280)], radius=6, fill="#FFFFFF", outline=GRAY_BORDER, width=1)
        draw.text((bx1 + 10, 212), b_title, fill=NAVY_DARK, font=box_title_font)
        draw.text((bx1 + 10, 232), b_desc, fill=GRAY_TEXT, font=body_font)

    # 4. Layer 2: Process Layer (X: 340 to 1220, Y: 320 to 650)
    draw.rounded_rectangle([(340, 320), (1220, 650)], radius=8, fill="#F8FAFC", outline=NAVY_MED, width=2)
    draw.rectangle([(340, 320), (1220, 355)], fill=NAVY_MED)
    draw.text((355, 328), "PROCESS LAYER (Core Business Intelligence & Orchestration)", fill="#FFFFFF", font=section_title_font)
    
    p_boxes = [
        ("Carrier Normalizer (DW 2.0)", "carrier-normalization.xml\nMaps BlueDart & Delhivery into\nUnified Canonical Event Model\nIST to UTC ISO-8601 Strings", 360, 620, 365, 485),
        ("Idempotency Engine", "shipment-processing.xml\nDeterministic Hash:\nevent_key = CARRIER-AWB-STATUS-TS\nReturns DUPLICATE_ACK (200)", 640, 920, 365, 485),
        ("Quarantine & Reconciliation", "subflow-quarantine-unknown\nBuffers Unmanifested Scans in DB\nAuto-Reconcile on Order Manifest\nOperator Replay Capability", 940, 1200, 365, 485),
        ("Anti-Regression State Engine", "flow-process-canonical-event\nStatus Rank Hierarchy (10 to 50)\nPrevents Stale Scan Rollback\nPreserves Forward Milestone", 360, 620, 505, 635),
        ("Explainable Delay Risk Engine", "risk-assessment.xml\nEvaluates Revised ETA vs Promised SLA\nGenerates Transparent Codes:\nON_TRACK, AT_RISK, DELAYED", 640, 920, 505, 635),
        ("Milestone Notification Filter", "notification-queue.xml\nFilters Major Milestone Transitions\nSuppresses Routine Transit Scans\nStages Alert in Outbox Table", 940, 1200, 505, 635),
    ]
    for b_title, b_desc, bx1, bx2, by1, by2 in p_boxes:
        draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=6, fill="#FFFFFF", outline=GRAY_BORDER, width=1)
        draw.text((bx1 + 10, by1 + 8), b_title, fill=NAVY_DARK, font=box_title_font)
        draw.text((bx1 + 10, by1 + 30), b_desc, fill=GRAY_TEXT, font=body_font)

    # 5. Layer 3: System Layer (X: 340 to 1220, Y: 680 to 910)
    draw.rounded_rectangle([(340, 680), (1220, 910)], radius=8, fill="#F0FDF4", outline="#15803D", width=2)
    draw.rectangle([(340, 680), (1220, 715)], fill="#15803D")
    draw.text((355, 688), "SYSTEM LAYER (Relational Persistence & Asynchronous Transport)", fill="#FFFFFF", font=section_title_font)
    
    s_boxes = [
        ("MySQL 8.0 Persistence Subflows", "database-operations.xml\nACID Operations across Relational Tables:\n- shipments (Master State & Risk Level)\n- shipment_tracking_events (Immutable Audit)\n- pending_tracking_events (Quarantine Buffer)\n- notification_outbox (Transactional Outbox)\n- integration_alerts (System Audit Trail)", 360, 840, 725, 895),
        ("Asynchronous Messaging Broker", "global-config.xml & notification-queue.xml\nPersistent Intra-JVM VM Queue:\nQueue: shipment-milestone-queue\nDecouples Ingress Webhook (<50ms ACK)\nGuarantees At-Least-Once Delivery", 860, 1200, 725, 895),
    ]
    for b_title, b_desc, bx1, bx2, by1, by2 in s_boxes:
        draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=6, fill="#FFFFFF", outline=GRAY_BORDER, width=1)
        draw.text((bx1 + 10, by1 + 8), b_title, fill=NAVY_DARK, font=box_title_font)
        draw.text((bx1 + 10, by1 + 30), b_desc, fill=GRAY_TEXT, font=body_font)

    # 6. Right Column: Future Scope & Roadmap (X: 1260 to 1570)
    # Highlighted with dashed outline and warning amber banner
    draw.rounded_rectangle([(1260, 100), (1570, 930)], radius=10, fill=FUTURE_BG, outline=FUTURE_BORDER, width=2)
    draw.rectangle([(1260, 100), (1570, 140)], fill=ACCENT_AMBER)
    draw.text((1275, 112), "FUTURE ENHANCEMENT SCOPE", fill="#FFFFFF", font=section_title_font)
    
    # Explanatory warning badge
    draw.rounded_rectangle([(1275, 155), (1555, 235)], radius=6, fill=ACCENT_AMBER_BG, outline=ACCENT_AMBER, width=1)
    draw.text((1285, 162), "CRITICAL ARCHITECTURAL DISTINCTION:", fill=ACCENT_AMBER, font=badge_font)
    draw.text((1285, 180), "SMTP Email and SMS delivery are\nNOT active in current build.\nCurrently, milestone alerts are\nsafely staged in notification_outbox.", fill=NAVY_DARK, font=note_font)
    
    future_items = [
        ("SMTP Live Email Gateway", "External SMTP Server Connection\n(e.g., SendGrid, Mailgun, Gmail)\nHTML Alert Templates for Customers\nStatus: Future Enhancement Only", 250, 360),
        ("SMS & WhatsApp Gateway", "Twilio / Gupshup Gateway Integration\nDirect-to-Phone Milestone Alerts\nCustomer Exception Notifications\nStatus: Future Enhancement Only", 380, 490),
        ("Anypoint MQ Cloud Broker", "Migration from local VM queue to\nAnypoint MQ distributed cloud queues\nfor multi-worker CloudHub clustering\nStatus: Future Enhancement Only", 510, 620),
        ("Cryptographic HMAC Auth", "Upgrade carrier token security to\nHMAC-SHA256 signature verification\nwith replay window timestamp check\nStatus: Future Enhancement Only", 640, 750),
        ("Physical 3-Tier Microservices", "Splitting logical layers into 3 isolated\nCloudHub apps: eapi, papi, sapi\nStatus: Future Enhancement Only", 770, 880),
    ]
    for f_title, f_desc, fy1, fy2 in future_items:
        draw.rounded_rectangle([(1275, fy1), (1555, fy2)], radius=6, fill="#FFFFFF", outline=FUTURE_BORDER, width=1)
        draw.text((1285, fy1 + 8), f_title, fill=NAVY_DARK, font=box_title_font)
        draw.text((1285, fy1 + 30), f_desc, fill=GRAY_TEXT, font=note_font)

    # 7. Directional Arrows and Labels
    # Ingress Arrow: External -> Experience Layer
    draw.line([(290, 210), (340, 210)], fill=NAVY_DARK, width=3)
    draw.polygon([(340, 210), (330, 204), (330, 216)], fill=NAVY_DARK)
    
    # Downward Arrow: Experience -> Process Layer
    draw.line([(780, 290), (780, 320)], fill=NAVY_DARK, width=3)
    draw.polygon([(780, 320), (774, 310), (786, 310)], fill=NAVY_DARK)
    
    # Downward Arrow: Process -> System Layer
    draw.line([(780, 650), (780, 680)], fill=NAVY_DARK, width=3)
    draw.polygon([(780, 680), (774, 670), (786, 670)], fill=NAVY_DARK)
    
    # Dashed Arrow to Future Scope
    for y_dash in range(750, 850, 10):
        draw.line([(1220, y_dash), (1240, y_dash)], fill=ACCENT_AMBER, width=2)
    draw.line([(1220, 800), (1260, 800)], fill=ACCENT_AMBER, width=2)
    draw.polygon([(1260, 800), (1250, 794), (1250, 806)], fill=ACCENT_AMBER)
    draw.text((1180, 810), "Future Link", fill=ACCENT_AMBER, font=badge_font)

    # Ensure output directory exists and save
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", dpi=(300, 300))
    print(f"Architecture diagram successfully generated at: {output_path}")

if __name__ == "__main__":
    out = "c:/Users/DELL/OneDrive/Desktop/Hackathon11/Cognizant-Hackathon/architecture_diagram.png"
    create_architecture_diagram(out)
