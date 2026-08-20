import io
import pandas as pd
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
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

def generate_student_pdf_report(student):
    """
    Generates an official 2-Page EduTrack Comprehensive Report Card in PDF format.
    Includes Executive KPIs, 7-Pillar HPI Breakdown, Subject Examination Marks,
    NLP Remarks, Gamification Badges, and Signature Block.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#1e293b'))
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=15, textColor=colors.HexColor('#64748b'))
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#0f172a'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=9.5, leading=13.5, textColor=colors.HexColor('#334155'))
    table_header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=colors.white)

    story = []

    # ==================== PAGE 1 ====================
    # Header Banner
    story.append(Paragraph("EDUTRACK — COMPREHENSIVE PROGRESS REPORT CARD", title_style))
    story.append(Paragraph(f"Official Academic, Attendance & Behavioral Analysis &bull; {student.full_name}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb'), spaceAfter=12))

    # Student Info Table
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
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
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
    score_color = colors.HexColor('#16a34a') if perf.holistic_score >= 75 else (colors.HexColor('#d97706') if perf.holistic_score >= 60 else colors.HexColor('#dc2626'))
    
    kpi_data = [
        [
            Paragraph(f"<font size=18 color='{score_color.hexval()}'><b>{perf.holistic_score} / 100</b></font><br/><font size=8 color='#64748b'>Holistic Score (HPI)</font>", body_style),
            Paragraph(f"<b>Risk Level:</b> <font color='{score_color.hexval()}'><b>{perf.get_risk_level_display()}</b></font><br/><font size=8 color='#64748b'>ML Predicted Final: {ml_pred['predicted_score']}% ({ml_pred['predicted_grade']})</font>", body_style),
            Paragraph(f"<b>Attendance:</b> {perf.attendance_score}%<br/><font size=8 color='#64748b'>Academic Avg: {perf.academic_score}%</font>", body_style)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[180, 200, 160])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#3b82f6')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 7-Pillars Breakdown Table
    story.append(Paragraph("7-Pillar Holistic Performance Index (HPI) Breakdown", h2_style))
    breakdown_data = [
        [Paragraph("Pillar Component", table_header_style), Paragraph("Score (%)", table_header_style), Paragraph("Weight", table_header_style), Paragraph("Status / Assessment", table_header_style)],
        [Paragraph("Academic Performance", body_style), Paragraph(f"{perf.academic_score}%", body_style), Paragraph("40%", body_style), Paragraph("Strong" if perf.academic_score>=75 else "Needs Attention", body_style)],
        [Paragraph("Attendance Compliance", body_style), Paragraph(f"{perf.attendance_score}%", body_style), Paragraph("15%", body_style), Paragraph("Good" if perf.attendance_score>=75 else "At Risk", body_style)],
        [Paragraph("Behaviour & Conduct", body_style), Paragraph(f"{perf.behaviour_score}%", body_style), Paragraph("15%", body_style), Paragraph("Satisfactory", body_style)],
        [Paragraph("Classroom Participation", body_style), Paragraph(f"{perf.participation_score}%", body_style), Paragraph("10%", body_style), Paragraph("Active Engagement", body_style)],
        [Paragraph("Assignments Completion", body_style), Paragraph(f"{perf.assignment_score}%", body_style), Paragraph("5%", body_style), Paragraph("On Track", body_style)],
        [Paragraph("Improvement Index", body_style), Paragraph(f"{perf.improvement_score}%", body_style), Paragraph("10%", body_style), Paragraph("Progressing Trajectory", body_style)],
        [Paragraph("Achievements & Honors", body_style), Paragraph(f"{perf.achievement_score}%", body_style), Paragraph("5%", body_style), Paragraph("Recognized", body_style)],
    ]
    b_table = Table(breakdown_data, colWidths=[180, 100, 100, 160])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(b_table)

    # PAGE BREAK TO ENSURE REPORT CARD IS AT LEAST 2 PAGES
    story.append(PageBreak())

    # ==================== PAGE 2 ====================
    story.append(Paragraph("EDUTRACK — ACADEMIC EXAMINATIONS & TEACHER REMARKS", title_style))
    story.append(Paragraph(f"Page 2 &bull; Subject Evaluation & Action Points for {student.full_name}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb'), spaceAfter=12))

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
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
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
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(nlp_table)
    story.append(Spacer(1, 12))

    # Gamification & Recognition Status
    story.append(Paragraph("Gamification Badges & Student Honors", h2_style))
    g_prof = StudentGamificationProfile.objects.filter(student=student).first()
    badges_qs = StudentBadge.objects.filter(student=student).select_related('badge')
    badge_titles = ", ".join([sb.badge.title for sb in badges_qs]) or "None unlocked yet."

    gamification_data = [
        [Paragraph(f"<b>Level & Title:</b> Level {g_prof.level if g_prof else 1} ({g_prof.rank_title if g_prof else 'Novice'})", body_style),
         Paragraph(f"<b>Total XP:</b> {g_prof.total_xp if g_prof else 0} XP", body_style),
         Paragraph(f"<b>Unlocked Badges:</b> {badge_titles}", body_style)]
    ]
    g_table = Table(gamification_data, colWidths=[200, 100, 240])
    g_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef3c7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#f59e0b')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(g_table)
    story.append(Spacer(1, 25))

    # Official Signature Block
    sig_data = [
        [
            Paragraph("________________________<br/><b>Class Teacher Signature</b>", body_style),
            Paragraph("________________________<br/><b>Principal / Director</b>", body_style),
            Paragraph("________________________<br/><b>Parent Signature</b>", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[180, 180, 180])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(sig_table)

    # Build 2-Page PDF document
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_performance_excel_file():
    """Generates Excel sheet of performance scores."""
    scores = PerformanceScore.objects.select_related('student', 'student__class_obj', 'student__division_obj').all()
    data = []
    for s in scores:
        data.append({
            'Student ID': s.student.student_id,
            'Student Name': s.student.full_name,
            'Class': f"{s.student.class_obj.name} - {s.student.division_obj.name}",
            'Academic Score (%)': float(s.academic_score),
            'Attendance Score (%)': float(s.attendance_score),
            'Behaviour Score (%)': float(s.behaviour_score),
            'Participation Score (%)': float(s.participation_score),
            'Assignment Score (%)': float(s.assignment_score),
            'Improvement Score (%)': float(s.improvement_score),
            'Achievement Score (%)': float(s.achievement_score),
            'Holistic Performance Index (HPI)': float(s.holistic_score),
            'Risk Level': s.risk_level,
        })
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Performance Score Report', index=False)
    buffer.seek(0)
    return buffer
