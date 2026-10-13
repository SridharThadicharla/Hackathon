import os
import re
from reportlab import platypus
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#666666"))
            # Header
            self.drawString(54, 755, "Shipment Signal Control Tower — Evaluator & Candidate Guide")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)
            # Footer
            self.line(54, 45, 558, 45)
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 32, page_text)
            self.drawString(54, 32, "Cognizant MuleSoft Hackathon 2026–2027 | Use Case 08: Logistics")
            self.restoreState()

def build_pdf():
    base_dir = r"c:\Users\DELL\OneDrive\Desktop\Hackathon11\Cognizant-Hackathon\Shipment-Tracking-Evaluator-Guide"
    output_pdf = os.path.join(base_dir, "Shipment-Tracking-Evaluator-Complete-Guide.pdf")

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#002B49'),
        spaceAfter=12,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        name='DocSubTitle',
        fontName='Helvetica',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#005A9C'),
        spaceAfter=20,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        name='SecHeading1',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#002B49'),
        spaceBefore=16,
        spaceAfter=6,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name='SecHeading2',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#005A9C'),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name='SecHeading3',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name='RegularText',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#222222'),
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name='BulletItem',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#222222'),
        leftIndent=12,
        spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        name='CodeSnippet',
        fontName='Courier',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F8FAFC'),
        borderColor=colors.HexColor('#CBD5E1'),
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=4,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='CalloutText',
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1E3A8A'),
        backColor=colors.HexColor('#EFF6FF'),
        borderColor=colors.HexColor('#93C5FD'),
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=4,
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#222222')
    ))
    styles.add(ParagraphStyle(
        name='TableHead',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    ))

    story = []

    # Title Page
    story.append(Spacer(1, 30))
    story.append(Paragraph("Shipment Signal Control Tower", styles['DocTitle']))
    story.append(Paragraph("Cognizant MuleSoft Hackathon 2026–2027 | Use Case 08: Logistics", styles['DocSubTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#005A9C'), spaceAfter=15))
    story.append(Paragraph("<b>Complete Project Architectural Explanation & Evaluator Preparation Guide</b>", styles['RegularText']))
    story.append(Paragraph("A comprehensive technical evaluation guide detailing the Mule 4 event-driven implementation, DataWeave canonical normalizers, MySQL relational schemas, MUnit test suite, and 15-minute interview evaluation strategy.", styles['RegularText']))
    story.append(Spacer(1, 15))

    meta_table_data = [
        [Paragraph("<b>Artifact Property</b>", styles['TableHead']), Paragraph("<b>Verified Details</b>", styles['TableHead'])],
        [Paragraph("Application Name", styles['TableCell']), Paragraph("Shipment-Signal-Control-Tower", styles['TableCell'])],
        [Paragraph("Runtime Target", styles['TableCell']), Paragraph("Mule Runtime 4.4.0 (Enterprise Edition)", styles['TableCell'])],
        [Paragraph("JDK Requirement", styles['TableCell']), Paragraph("OpenJDK 8 (1.8) or OpenJDK 11", styles['TableCell'])],
        [Paragraph("Persistence Layer", styles['TableCell']), Paragraph("MySQL 8.0 (InnoDB) with UTC timezone", styles['TableCell'])],
        [Paragraph("Messaging Layer", styles['TableCell']), Paragraph("Persistent FIFO VM Queue + Transactional Outbox", styles['TableCell'])],
        [Paragraph("Specification", styles['TableCell']), Paragraph("RAML 1.0 (Contract-First APIKit Routing)", styles['TableCell'])],
        [Paragraph("Automated Tests", styles['TableCell']), Paragraph("9 MUnit 2.3 Automated Test Suites (100% Pass)", styles['TableCell'])],
        [Paragraph("Manual Scenarios", styles['TableCell']), Paragraph("16 Postman Automated Requests across 4 Folders", styles['TableCell'])],
        [Paragraph("Document Count", styles['TableCell']), Paragraph("31 Markdown Chapters + Combined Master PDF", styles['TableCell'])],
    ]
    t = Table(meta_table_data, colWidths=[140, 360])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Generated automatically from verified project codebase and test definitions.</i>", styles['RegularText']))
    story.append(PageBreak())

    doc_files = [
        "README.md",
        "00-START-HERE.md",
        "01-Project-Overview.md",
        "02-API-Led-Architecture.md",
        "03-Project-Structure-and-File-Inventory.md",
        "04-Installation-and-Project-Startup.md",
        "05-RAML-Files-Explained.md",
        "06-Global-Configurations-and-Properties.md",
        "07-Flow-Execution-Order.md",
        "08-Flow-by-Flow-Explanation.md",
        "09-Connector-Reference.md",
        "10-DataWeave-and-Carrier-Mappings.md",
        "11-Database-Tables-and-SQL.md",
        "12-End-to-End-Execution.md",
        "13-Authentication-and-Security.md",
        "14-Error-Handling-and-Retry.md",
        "15-MUnit-Tests-Explained.md",
        "16-Postman-and-Manual-Testing.md",
        "17-Negative-Scenarios-and-Recovery.md",
        "18-Queue-and-Notification-Processing.md",
        "19-Logging-and-Monitoring.md",
        "20-Deployment-and-API-Management.md",
        "21-Requirements-Traceability.md",
        "22-Technical-Decisions-and-Tradeoffs.md",
        "23-Team-Contribution-and-Evaluator-Questions.md",
        "24-15-Minute-Interview-Preparation.md",
        "25-Troubleshooting.md",
        "26-Known-Limitations-and-Future-Scope.md",
        "27-Glossary.md",
        "28-Quick-Revision-Cheat-Sheet.md",
        "29-DOCUMENTATION-VERIFICATION-REPORT.md"
    ]

    def clean_text_for_xml(s):
        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        return s

    def format_inline(text):
        # Escape raw XML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Protect inline code `...`
        code_tokens = []
        def code_sub(m):
            idx = len(code_tokens)
            content = m.group(1)
            code_tokens.append(f'<font face="Courier" color="#0F172A"><b>{content}</b></font>')
            return f"___CODE_TOKEN_{idx}___"
        text = re.sub(r'`(.*?)`', code_sub, text)

        # Bold **...**
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

        # Italic *...* (only if surrounded by non-space)
        text = re.sub(r'(?<!\w)\*([^*]+?)\*(?!\w)', r'<i>\1</i>', text)

        # Links [text](url)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<u>\1</u>', text)

        # Restore code tokens
        for idx, token in enumerate(code_tokens):
            text = text.replace(f"___CODE_TOKEN_{idx}___", token)

        return text

    def create_table_flowable(rows):
        if not rows:
            return Spacer(1, 1)
        num_cols = max(len(r) for r in rows)
        norm_rows = []
        for r_idx, r in enumerate(rows):
            new_r = []
            is_head = (r_idx == 0)
            cell_style = styles['TableHead'] if is_head else styles['TableCell']
            for c in r:
                formatted_c = format_inline(c)
                try:
                    p = Paragraph(formatted_c, cell_style)
                except Exception:
                    p = Paragraph(clean_text_for_xml(c), cell_style)
                new_r.append(p)
            while len(new_r) < num_cols:
                new_r.append(Paragraph("", cell_style))
            norm_rows.append(new_r)

        avail_width = 504.0
        col_w = avail_width / num_cols
        t = Table(norm_rows, colWidths=[col_w] * num_cols)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]))
        return t

    def md_to_reportlab(content):
        elements = []
        lines = content.split('\n')
        i = 0
        in_code_block = False
        code_lines = []
        in_table = False
        table_rows = []

        while i < len(lines):
            line = lines[i]

            if line.strip().startswith('```'):
                if in_code_block:
                    in_code_block = False
                    code_text = clean_text_for_xml('\n'.join(code_lines[:45]))
                    if len(code_lines) > 45:
                        code_text += "\n... [content truncated for space] ..."
                    elements.append(Paragraph(code_text.replace('\n', '<br/>'), styles['CodeSnippet']))
                    code_lines = []
                else:
                    if in_table and table_rows:
                        elements.append(create_table_flowable(table_rows))
                        table_rows = []
                        in_table = False
                    in_code_block = True
                    code_lines = []
                i += 1
                continue

            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # Table row
            if '|' in line and not line.strip().startswith('>'):
                stripped = line.strip()
                if stripped.startswith('|') and stripped.endswith('|'):
                    cells = [c.strip() for c in stripped.split('|')[1:-1]]
                    if all(re.match(r'^:?-+:?$', c) for c in cells):
                        i += 1
                        continue
                    in_table = True
                    table_rows.append(cells)
                    i += 1
                    continue

            if in_table:
                if table_rows:
                    elements.append(create_table_flowable(table_rows))
                    table_rows = []
                in_table = False

            stripped = line.strip()
            if not stripped:
                i += 1
                continue

            try:
                if stripped.startswith('# '):
                    h_text = clean_text_for_xml(stripped[2:])
                    elements.append(Paragraph(h_text, styles['SecHeading1']))
                    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#005A9C'), spaceAfter=6))
                elif stripped.startswith('## '):
                    h_text = clean_text_for_xml(stripped[3:])
                    elements.append(Paragraph(h_text, styles['SecHeading2']))
                elif stripped.startswith('### '):
                    h_text = clean_text_for_xml(stripped[4:])
                    elements.append(Paragraph(h_text, styles['SecHeading3']))
                elif stripped.startswith('#### '):
                    h_text = clean_text_for_xml(stripped[5:])
                    elements.append(Paragraph(f"<b>{h_text}</b>", styles['RegularText']))
                elif stripped.startswith('> '):
                    c_text = format_inline(stripped[2:])
                    elements.append(Paragraph(c_text, styles['CalloutText']))
                elif stripped.startswith('- ') or stripped.startswith('* '):
                    b_text = format_inline(stripped[2:])
                    elements.append(Paragraph(f"&bull; {b_text}", styles['BulletItem']))
                elif re.match(r'^\d+\.\s', stripped):
                    match = re.match(r'^(\d+\.)\s(.*)$', stripped)
                    num = match.group(1)
                    b_text = format_inline(match.group(2))
                    elements.append(Paragraph(f"<b>{num}</b> {b_text}", styles['BulletItem']))
                elif stripped == '---':
                    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=5, spaceAfter=5))
                else:
                    p_text = format_inline(stripped)
                    elements.append(Paragraph(p_text, styles['RegularText']))
            except Exception:
                # Fallback to plain text if malformed inline tags
                elements.append(Paragraph(clean_text_for_xml(stripped), styles['RegularText']))

            i += 1

        if in_table and table_rows:
            elements.append(create_table_flowable(table_rows))

        return elements

    for doc_file in doc_files:
        file_path = os.path.join(base_dir, doc_file)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            story.extend(md_to_reportlab(content))
            story.append(Spacer(1, 10))
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF at: {output_pdf}")
    print(f"File size: {os.path.getsize(output_pdf)} bytes")

if __name__ == "__main__":
    build_pdf()
