import io
import os
from django.conf import settings
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String, Group, Polygon

def get_edutrack_logo_path():
    """Returns absolute file path to edutrack_logo.png with fallback resolution."""
    possible_paths = [
        str(settings.BASE_DIR / 'static' / 'images' / 'edutrack_logo.png'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'edutrack_logo.png'),
        r'C:\Users\Daksh Shah\.gemini\antigravity\scratch\edutrack\static\images\edutrack_logo.png',
        r'C:\Users\Daksh Shah\.gemini\antigravity\scratch\Student360\static\images\edutrack_logo.png',
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def generate_award_certificate_pdf(award):
    """
    Generates an official high-prestige Student of the Month Recognition Certificate PDF featuring:
    - High-res EduTrack Branding Logo Header
    - Dual Ornate Gold Canvas Border with Sunflower Rosette Embellishments
    - Off-white Cream Background (#FAF8F5)
    - Emerald Green (#064E3B) & Gold (#D4AF37) Serif Typography
    - Official Stamp Seal & Double Signature Block
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    # Color Palette Definition
    CREAM_BG = colors.HexColor('#FAF8F5')
    DARK_EMERALD = colors.HexColor('#064E3B')
    SHINING_EMERALD = colors.HexColor('#047857')
    GOLD_ACCENT = colors.HexColor('#D4AF37')
    SUNFLOWER_YELLOW = colors.HexColor('#F59E0B')
    SUNFLOWER_GOLD = colors.HexColor('#FEF08A')
    TEXT_MUTED = colors.HexColor('#475569')

    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=32,
        leading=38,
        alignment=TA_CENTER,
        textColor=DARK_EMERALD
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
        fontSize=30,
        leading=36,
        alignment=TA_CENTER,
        textColor=SHINING_EMERALD
    )

    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12.5,
        leading=18,
        alignment=TA_CENTER,
        textColor=DARK_EMERALD
    )

    subtitle_style = ParagraphStyle(
        'CertSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=TEXT_MUTED
    )

    story = []

    # Top Decorative Canvas Frame Drawing
    d = Drawing(742, 42)
    d.add(Rect(0, 0, 742, 42, fillColor=CREAM_BG, strokeColor=GOLD_ACCENT, strokeWidth=1.5))
    d.add(Circle(25, 21, 10, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d.add(Circle(25, 21, 5, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))
    d.add(Circle(717, 21, 10, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d.add(Circle(717, 21, 5, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))
    story.append(d)
    story.append(Spacer(1, 8))

    # EduTrack Logo Header
    logo_path = get_edutrack_logo_path()
    if logo_path:
        logo_img = Image(logo_path, width=450, height=300)
        logo_img.hAlign = 'CENTER'
        story.append(logo_img)
        story.append(Spacer(1, 4))

    # Main Certificate Text
    story.append(Paragraph("EDUTRACK ACADEMY OF EXCELLENCE", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("CERTIFICATE OF RECOGNITION", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("THIS CERTIFICATE IS PROUDLY PRESENTED TO", subtitle_style))
    story.append(Spacer(1, 12))
    
    # Student Name Block with Gold Accent Lines
    story.append(Paragraph(f"<u>&nbsp; {award.student.full_name.upper()} &nbsp;</u>", name_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"For Outstanding Academic & Behavioral Performance as <b>{award.get_award_type_display()}</b>", award_title_style))
    story.append(Spacer(1, 10))

    details = f"Class: <b>{award.student.class_obj.name} — Division {award.student.division_obj.name}</b> &bull; Academic Year: <b>{award.year}</b>"
    story.append(Paragraph(details, body_style))
    story.append(Spacer(1, 10))

    reason_text = award.reason or "Demonstrated remarkable academic diligence, exemplary behaviour, and holistic performance."
    story.append(Paragraph(f"<i>&ldquo;{reason_text}&rdquo;</i>", body_style))
    story.append(Spacer(1, 25))

    # Signature & Gold Stamp Seal Table Section
    footer_data = [
        [
            Paragraph("________________________<br/><b>Principal / Director</b>", body_style),
            Paragraph("<font color='#D4AF37' size=12><b>★ OFFICIAL SEAL ★</b></font><br/><font size=8.5 color='#475569'>Certificate ID: CERT-EDU-00" + str(award.id) + "</font>", ParagraphStyle('SealText', parent=body_style, fontName='Times-Bold')),
            Paragraph("________________________<br/><b>Academic Head</b>", body_style)
        ]
    ]

    table = Table(footer_data, colWidths=[240, 260, 240])
    table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(table)

    # Bottom Decorative Canvas Frame Drawing
    d_bottom = Drawing(742, 36)
    d_bottom.add(Rect(0, 0, 742, 36, fillColor=CREAM_BG, strokeColor=GOLD_ACCENT, strokeWidth=1.5))
    d_bottom.add(Circle(25, 18, 9, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d_bottom.add(Circle(25, 18, 4, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))
    d_bottom.add(Circle(717, 18, 9, fillColor=SUNFLOWER_YELLOW, strokeColor=GOLD_ACCENT, strokeWidth=1))
    d_bottom.add(Circle(717, 18, 4, fillColor=colors.HexColor('#6B4226'), strokeColor=colors.HexColor('#4A2E1B'), strokeWidth=0.5))

    story.append(Spacer(1, 10))
    story.append(d_bottom)

    doc.build(story)
    buffer.seek(0)
    return buffer
