import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String, Group, Polygon

def generate_award_certificate_pdf(award):
    """
    Generates a minimalist recognition certificate template featuring:
    - Watercolor yellow sunflowers & botanical green leaves bordering the corners
    - Off-white central background (#FDFBF7)
    - Clean dark green (#1B4332) & gold (#D4AF37) elegant serif text layout
    - Professional recognition award layout
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # Color Palette Definition
    OFF_WHITE = colors.HexColor('#FDFBF7')
    DARK_GREEN = colors.HexColor('#1B4332')
    BOTANICAL_GREEN = colors.HexColor('#2D6A4F')
    GOLD_ACCENT = colors.HexColor('#D4AF37')
    SUNFLOWER_YELLOW = colors.HexColor('#F4A261')
    SUNFLOWER_GOLD = colors.HexColor('#E9C46A')
    TEXT_MUTED = colors.HexColor('#52796F')

    title_style = ParagraphStyle(
        'SunflowerTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=32,
        leading=38,
        alignment=TA_CENTER,
        textColor=DARK_GREEN
    )

    award_title_style = ParagraphStyle(
        'AwardTitle',
        parent=styles['Normal'],
        fontName='Times-BoldItalic',
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=GOLD_ACCENT
    )

    name_style = ParagraphStyle(
        'StudentName',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
        textColor=DARK_GREEN
    )

    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        textColor=BOTANICAL_GREEN
    )

    subtitle_style = ParagraphStyle(
        'CertSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=TEXT_MUTED
    )

    story = []

    # Outer Decorative Botanical Canvas Page Frame Drawing
    d = Drawing(732, 50)
    # Background off-white fill
    d.add(Rect(0, 0, 732, 50, fillColor=OFF_WHITE, strokeColor=GOLD_ACCENT, strokeWidth=1.5))
    
    # Corner Sunflower & Leaf Botanical Embellishments
    # Top-Left Sunflower Accent
    d.add(Circle(25, 25, 12, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d.add(Circle(25, 25, 6, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))
    d.add(Circle(12, 25, 5, fillColor=SUNFLOWER_GOLD, strokeColor=colors.HexColor('#D4AF37'), strokeWidth=0.5))
    d.add(Circle(38, 25, 5, fillColor=SUNFLOWER_GOLD, strokeColor=colors.HexColor('#D4AF37'), strokeWidth=0.5))
    d.add(Circle(25, 12, 5, fillColor=SUNFLOWER_GOLD, strokeColor=colors.HexColor('#D4AF37'), strokeWidth=0.5))
    d.add(Circle(25, 38, 5, fillColor=SUNFLOWER_GOLD, strokeColor=colors.HexColor('#D4AF37'), strokeWidth=0.5))

    # Top-Right Sunflower Accent
    d.add(Circle(707, 25, 12, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d.add(Circle(707, 25, 6, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))
    d.add(Circle(694, 25, 5, fillColor=SUNFLOWER_GOLD, strokeColor=colors.HexColor('#D4AF37'), strokeWidth=0.5))
    d.add(Circle(720, 25, 5, fillColor=SUNFLOWER_GOLD, strokeColor=colors.HexColor('#D4AF37'), strokeWidth=0.5))
    
    story.append(d)
    story.append(Spacer(1, 15))

    # Main Certificate Text Story
    story.append(Paragraph("STUDENT360 ACADEMY OF EXCELLENCE", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Certificate of Recognition", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("THIS CERTIFICATE IS PROUDLY PRESENTED TO", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(award.student.full_name.upper(), name_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"For Outstanding Achievement as <b>{award.get_award_type_display()}</b>", award_title_style))
    story.append(Spacer(1, 12))

    details = f"Class {award.student.class_obj.name} — Division {award.student.division_obj.name} &bull; Academic Year {award.year}"
    story.append(Paragraph(details, body_style))
    story.append(Spacer(1, 12))

    reason_text = award.reason or "Demonstrated remarkable academic diligence, exemplary behaviour, and holistic excellence."
    story.append(Paragraph(f"<i>&ldquo;{reason_text}&rdquo;</i>", body_style))
    story.append(Spacer(1, 35))

    # Signature & Seal Table Section
    footer_data = [
        [
            Paragraph("________________________<br/><b>Principal / Director</b>", body_style),
            Paragraph("<font color='#D4AF37'><b>★ OFFICIAL SEAL ★</b></font><br/><font size=8 color='#52796F'>Certificate ID: CERT-360-00" + str(award.id) + "</font>", ParagraphStyle('SealText', parent=body_style, fontName='Times-Bold')),
            Paragraph("________________________<br/><b>Academic Head</b>", body_style)
        ]
    ]

    table = Table(footer_data, colWidths=[240, 240, 240])
    table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(table)

    # Bottom Botanical Sunflower Border Drawing
    d_bottom = Drawing(732, 40)
    d_bottom.add(Rect(0, 0, 732, 40, fillColor=OFF_WHITE, strokeColor=GOLD_ACCENT, strokeWidth=1.5))
    
    # Bottom Left Botanical Leaf
    d_bottom.add(Circle(25, 20, 10, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d_bottom.add(Circle(25, 20, 5, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))
    
    # Bottom Right Botanical Leaf
    d_bottom.add(Circle(707, 20, 10, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d_bottom.add(Circle(707, 20, 5, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))

    story.append(Spacer(1, 15))
    story.append(d_bottom)

    doc.build(story)
    buffer.seek(0)
    return buffer
