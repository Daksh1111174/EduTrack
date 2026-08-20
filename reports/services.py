import io
import os
import pandas as pd
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from performance.models import PerformanceScore
from performance.services import calculate_student_hpi
from academics.models import Mark
from remarks.models import TeacherRemark
from awards.models import StudentAward
from meetings.models import ParentTeacherMeeting
from gamification.models import StudentGamificationProfile, StudentBadge
from performance.ml_engine import predict_student_performance
from remarks.nlp_engine import analyze_teacher_remarks_nlp

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

def generate_student_pdf_report(student):
    """
    Generates an executive, highly attractive 2-Page EduTrack Comprehensive Report Card in PDF format featuring:
    - High-res EduTrack Branding Logo Header
    - Executive Performance KPI Box
    - 7-Pillar HPI Breakdown Table with Alternate Striping
    - Subject Examination Marks & Letter Grades
    - AI NLP Teacher Remarks & Action Plan
    - Official Signature Block
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#0F172A'))
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=14, textColor=colors.HexColor('#64748B'))
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=9.5, leading=13.5, textColor=colors.HexColor('#334155'))
    table_header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=colors.white)

    story = []

    logo_path = get_edutrack_logo_path()

    # ==================== PAGE 1 ====================
    # Header Banner with Branding Logo
    if logo_path:
        header_data = [
            [
                Image(logo_path, width=240, height=160),
                [
                    Paragraph("EDUTRACK — COMPREHENSIVE PROGRESS REPORT CARD", title_style),
                    Paragraph(f"Official Academic, Attendance & Behavioral Analysis &bull; {student.full_name}", subtitle_style)
                ]
            ]
        ]
        header_table = Table(header_data, colWidths=[250, 290])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph("EDUTRACK — COMPREHENSIVE PROGRESS REPORT CARD", title_style))
        story.append(Paragraph(f"Official Academic, Attendance & Behavioral Analysis &bull; {student.full_name}", subtitle_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=12))

    # Student Profile Metadata Table
    info_data = [
        [Paragraph("<b>Student ID:</b>", body_style), Paragraph(student.student_id, body_style),
         Paragraph("<b>Class & Division:</b>", body_style), Paragraph(f"{student.class_obj.name} - {student.division_obj.name}", body_style)],
        [Paragraph("<b>Roll Number:</b>", body_style), Paragraph(str(student.roll_number), body_style),
         Paragraph("<b>Academic Year:</b>", body_style), Paragraph(str(student.academic_year or '2025-2026'), body_style)],
        [Paragraph("<b>Gender:</b>", body_style), Paragraph(student.get_gender_display() if hasattr(student, 'get_gender_display') else student.gender, body_style),
         Paragraph("<b>Contact Email:</b>", body_style), Paragraph(student.email or 'N/A', body_style)],
    ]
    info_table = Table(info_data, colWidths=[110, 160, 110, 160])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    perf = PerformanceScore.objects.filter(student=student).first()
    if not perf:
        perf = calculate_student_hpi(student)

    ml_pred = predict_student_performance(student)

    # Executive KPI Summary Box
    story.append(Paragraph("Executive Performance KPIs & Risk Status", h2_style))
    score_color = colors.HexColor('#16A34A') if perf.holistic_score >= 75 else (colors.HexColor('#D97706') if perf.holistic_score >= 60 else colors.HexColor('#DC2626'))
    
    kpi_data = [
        [
            Paragraph(f"<font size=18 color='{score_color.hexval()}'><b>{perf.holistic_score} / 100</b></font><br/><font size=8.5 color='#64748B'>Holistic Score (HPI)</font>", body_style),
            Paragraph(f"<b>Risk Status:</b> <font color='{score_color.hexval()}'><b>{perf.get_risk_level_display()}</b></font><br/><font size=8.5 color='#64748B'>ML Predicted Final: {ml_pred['predicted_score']}% ({ml_pred['predicted_grade']})</font>", body_style),
            Paragraph(f"<b>Attendance Compliance:</b> {perf.attendance_score}%<br/><font size=8.5 color='#64748B'>Academic Examination Avg: {perf.academic_score}%</font>", body_style)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[180, 200, 160])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#3B82F6')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 7-Pillars HPI Breakdown Table
    story.append(Paragraph("7-Pillar Holistic Performance Index (HPI) Breakdown", h2_style))
    breakdown_data = [
        [Paragraph("Pillar Component", table_header_style), Paragraph("Score (%)", table_header_style), Paragraph("Weight", table_header_style), Paragraph("Status / Assessment", table_header_style)],
        [Paragraph("Academic Performance", body_style), Paragraph(f"{perf.academic_score}%", body_style), Paragraph("35%", body_style), Paragraph("Strong" if perf.academic_score>=75 else "Needs Attention", body_style)],
        [Paragraph("Attendance Compliance", body_style), Paragraph(f"{perf.attendance_score}%", body_style), Paragraph("25%", body_style), Paragraph("Good" if perf.attendance_score>=75 else "At Risk", body_style)],
        [Paragraph("Behaviour & Conduct", body_style), Paragraph(f"{perf.behaviour_score}%", body_style), Paragraph("15%", body_style), Paragraph("Satisfactory", body_style)],
        [Paragraph("Classroom Participation", body_style), Paragraph(f"{perf.participation_score}%", body_style), Paragraph("10%", body_style), Paragraph("Active Engagement", body_style)],
        [Paragraph("Assignments Completion", body_style), Paragraph(f"{perf.assignment_score}%", body_style), Paragraph("5%", body_style), Paragraph("On Track", body_style)],
        [Paragraph("Improvement Index", body_style), Paragraph(f"{perf.improvement_score}%", body_style), Paragraph("5%", body_style), Paragraph("Progressing Trajectory", body_style)],
        [Paragraph("Achievements & Honors", body_style), Paragraph(f"{perf.achievement_score}%", body_style), Paragraph("5%", body_style), Paragraph("Recognized", body_style)],
    ]
    b_table = Table(breakdown_data, colWidths=[180, 100, 100, 160])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,7), (-1,7), colors.HexColor('#FFFFFF')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(b_table)

    # PAGE BREAK FOR PAGE 2
    story.append(PageBreak())

    # ==================== PAGE 2 ====================
    if logo_path:
        header2_data = [
            [
                Image(logo_path, width=210, height=140),
                [
                    Paragraph("EDUTRACK — ACADEMIC EXAMINATIONS & TEACHER REMARKS", title_style),
                    Paragraph(f"Page 2 &bull; Subject Evaluation & Action Points for {student.full_name}", subtitle_style)
                ]
            ]
        ]
        header2_table = Table(header2_data, colWidths=[220, 320])
        header2_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header2_table)
    else:
        story.append(Paragraph("EDUTRACK — ACADEMIC EXAMINATIONS & TEACHER REMARKS", title_style))
        story.append(Paragraph(f"Page 2 &bull; Subject Evaluation & Action Points for {student.full_name}", subtitle_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=12))

    # Subject Examination Marks Table
    story.append(Paragraph("Detailed Subject Examination Results", h2_style))
    marks_qs = Mark.objects.filter(student=student).select_related('exam', 'exam__subject').order_by('-exam__date')[:10]
    
    marks_table_data = [
        [Paragraph("Subject", table_header_style), Paragraph("Exam Name", table_header_style), Paragraph("Marks Obtained", table_header_style), Paragraph("Max Marks", table_header_style), Paragraph("Percentage", table_header_style), Paragraph("Grade", table_header_style)]
    ]
    if marks_qs.exists():
        for m in marks_qs:
            pct = m.percentage
            grade = 'A+' if pct >= 90 else ('A' if pct >= 80 else ('B' if pct >= 70 else ('C' if pct >= 60 else 'D')))
            marks_table_data.append([
                Paragraph(m.exam.subject.name, body_style),
                Paragraph(m.exam.name, body_style),
                Paragraph(str(m.marks_obtained), body_style),
                Paragraph(str(m.exam.max_marks), body_style),
                Paragraph(f"{pct}%", body_style),
                Paragraph(f"<b>{grade}</b>", body_style)
            ])
    else:
        marks_table_data.append([Paragraph("No published exam marks.", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style)])

    m_table = Table(marks_table_data, colWidths=[130, 150, 80, 80, 50, 50])
    m_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(m_table)
    story.append(Spacer(1, 12))

    # NLP Teacher Remarks & Recommendations
    story.append(Paragraph("AI Teacher Remark Extraction & Actionable Feedback", h2_style))
    nlp = analyze_teacher_remarks_nlp(student)
    
    strengths_str = ", ".join(nlp['strengths'])
    weaknesses_str = ", ".join(nlp['weaknesses'])
    recs_str = " ".join(nlp['recommendations'])

    nlp_data = [
        [Paragraph("<b>Key Strengths:</b>", body_style), Paragraph(strengths_str, body_style)],
        [Paragraph("<b>Areas for Growth:</b>", body_style), Paragraph(weaknesses_str, body_style)],
        [Paragraph("<b>Actionable Advice:</b>", body_style), Paragraph(recs_str, body_style)]
    ]
    nlp_table = Table(nlp_data, colWidths=[130, 410])
    nlp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(nlp_table)
    story.append(Spacer(1, 16))

    # Official Signature & Verification Block
    story.append(Paragraph("Official Verification & Signatures", h2_style))
    sig_data = [
        [
            Paragraph("________________________<br/><b>Class Teacher Signature</b>", body_style),
            Paragraph("<font color='#2563EB'><b>★ VERIFIED OFFICIAL DOCUMENT ★</b></font><br/><font size=8 color='#64748B'>Generated via EduTrack Platform</font>", ParagraphStyle('SigCenter', parent=body_style, alignment=1)),
            Paragraph("________________________<br/><b>Principal / Director</b>", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[180, 180, 180])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

def export_performance_excel_file():
    """Exports school-wide student performance scores as an Excel spreadsheet."""
    scores = PerformanceScore.objects.select_related('student', 'student__class_obj', 'student__division_obj').all()
    data = []
    for s in scores:
        data.append({
            'Student ID': s.student.student_id,
            'Student Name': s.student.full_name,
            'Class': s.student.class_obj.name,
            'Division': s.student.division_obj.name,
            'Academic Score': s.academic_score,
            'Attendance Score': s.attendance_score,
            'Behaviour Score': s.behaviour_score,
            'Participation Score': s.participation_score,
            'Assignment Score': s.assignment_score,
            'Improvement Score': s.improvement_score,
            'Holistic HPI Score': s.holistic_score,
            'Risk Level': s.risk_level,
        })
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Performance Analytics')
    buffer.seek(0)
    return buffer
