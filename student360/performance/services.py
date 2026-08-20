import datetime
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from academics.models import AcademicYear, Mark, Exam
from attendance.models import Attendance
from behaviour.models import BehaviourRecord
from assignments.models import AssignmentSubmission
from participation.models import Participation
from achievements.models import Achievement
from performance.models import PerformanceSetting, PerformanceScore

def get_active_setting(academic_year=None):
    if not academic_year:
        academic_year = AcademicYear.objects.filter(is_active=True).first()
    if not academic_year:
        # Fallback if no academic year exists yet
        return None
    setting, _ = PerformanceSetting.objects.get_or_create(academic_year=academic_year)
    return setting

def calculate_academic_score(student, month=None, year=None):
    """Calculate academic average percentage for student in the given month/year or overall."""
    marks_qs = Mark.objects.filter(student=student)
    if month and year:
        marks_qs = marks_qs.filter(exam__date__month=month, exam__date__year=year)
    
    if not marks_qs.exists():
        # Fallback to all historical marks if current month has no exams
        marks_qs = Mark.objects.filter(student=student)

    if not marks_qs.exists():
        return 75.0  # Neutral baseline for new students without exam records

    percentages = [mark.percentage for mark in marks_qs if mark.exam.max_marks > 0]
    if not percentages:
        return 75.0
    return round(sum(percentages) / len(percentages), 2)

def calculate_attendance_score(student, month=None, year=None):
    """Calculate attendance percentage score: (Present + 0.5 * Late) / Total * 100."""
    att_qs = Attendance.objects.filter(student=student)
    if month and year:
        att_qs = att_qs.filter(date__month=month, date__year=year)

    total_days = att_qs.count()
    if total_days == 0:
        # Fallback to all records
        att_qs = Attendance.objects.filter(student=student)
        total_days = att_qs.count()

    if total_days == 0:
        return 90.0  # Default assumption for new student

    p_count = att_qs.filter(status=Attendance.Status.PRESENT).count()
    l_count = att_qs.filter(status=Attendance.Status.LATE).count()
    leave_count = att_qs.filter(status=Attendance.Status.LEAVE).count()

    # Effective present days
    effective_present = p_count + (0.5 * l_count) + (0.8 * leave_count)
    pct = (effective_present / total_days) * 100.0
    return round(min(100.0, pct), 2)

def calculate_behaviour_score(student, month=None, year=None):
    """Calculate average behaviour rating (1-5) scaled to 100%."""
    records = BehaviourRecord.objects.filter(student=student)
    if month and year:
        records = records.filter(date__month=month, date__year=year)

    if not records.exists():
        records = BehaviourRecord.objects.filter(student=student)

    if not records.exists():
        return 80.0  # Default baseline rating (4.0/5.0)

    avg_ratings = [r.average_rating for r in records]
    overall_avg = sum(avg_ratings) / len(avg_ratings)
    score_pct = (overall_avg / 5.0) * 100.0
    return round(score_pct, 2)

def calculate_participation_score(student, month=None, year=None):
    """Calculate participation rating scaled to 100%."""
    records = Participation.objects.filter(student=student)
    if month and year:
        records = records.filter(date__month=month, date__year=year)

    if not records.exists():
        records = Participation.objects.filter(student=student)

    if not records.exists():
        return 75.0

    avg_ratings = [r.average_rating for r in records]
    overall_avg = sum(avg_ratings) / len(avg_ratings)
    return round((overall_avg / 5.0) * 100.0, 2)

def calculate_assignment_score(student, month=None, year=None):
    """Calculate assignment score combining average grade % and completion %."""
    subs = AssignmentSubmission.objects.filter(student=student)
    if month and year:
        subs = subs.filter(assignment__due_date__month=month, assignment__due_date__year=year)

    if not subs.exists():
        subs = AssignmentSubmission.objects.filter(student=student)

    if not subs.exists():
        return 80.0

    total_assignments = subs.count()
    completed = subs.filter(Q(status=AssignmentSubmission.Status.SUBMITTED) | Q(status=AssignmentSubmission.Status.GRADED)).count()
    completion_rate = (completed / total_assignments) * 100.0 if total_assignments > 0 else 100.0

    graded_subs = [s.percentage for s in subs if s.marks_obtained is not None]
    avg_marks = sum(graded_subs) / len(graded_subs) if graded_subs else 80.0

    combined = (0.7 * avg_marks) + (0.3 * completion_rate)
    return round(min(100.0, combined), 2)

def calculate_improvement_score(student, academic_year, month, year):
    """Calculate normalized improvement score based on trajectory from previous month/term."""
    # Find previous score record
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    prev_score = PerformanceScore.objects.filter(
        student=student,
        academic_year=academic_year,
        month=prev_month,
        year=prev_year
    ).first()

    if not prev_score:
        return 75.0  # Base neutral improvement score when no prior month baseline exists

    # Calculate raw current performance (excluding improvement)
    current_acad = calculate_academic_score(student, month, year)
    current_att = calculate_attendance_score(student, month, year)

    prev_raw = float(prev_score.academic_score) * 0.7 + float(prev_score.attendance_score) * 0.3
    curr_raw = float(current_acad) * 0.7 + float(current_att) * 0.3

    diff = curr_raw - prev_raw
    # Scaling: +10 point increase gives 90%, 0 diff gives 75%, -10 point drop gives 50%
    imp_score = 75.0 + (diff * 1.5)
    return round(max(0.0, min(100.0, imp_score)), 2)

def calculate_achievement_score(student, month=None, year=None):
    """Calculate achievement score based on accumulated points, capped at 100."""
    achievements = Achievement.objects.filter(student=student)
    if month and year:
        achievements = achievements.filter(date__month=month, date__year=year)

    if not achievements.exists():
        achievements = Achievement.objects.filter(student=student)

    total_points = achievements.aggregate(total=Sum('points'))['total'] or 0
    # 50 points = 100% score
    score = (total_points / 50.0) * 100.0
    return round(min(100.0, max(50.0 if total_points > 0 else 60.0, score)), 2)

from performance.risk_engine import evaluate_student_risk

def calculate_student_hpi(student, academic_year=None, month=None, year=None):
    """
    Core engine to compute Holistic Performance Index (HPI) for a student.
    Uses configurable weights from PerformanceSetting.
    """
    now = timezone.now()
    if not month: month = now.month
    if not year: year = now.year

    if not academic_year:
        academic_year = student.academic_year or AcademicYear.objects.filter(is_active=True).first()

    setting = get_active_setting(academic_year)

    w_acad = float(setting.weight_academic) if setting else 40.0
    w_att = float(setting.weight_attendance) if setting else 15.0
    w_beh = float(setting.weight_behaviour) if setting else 15.0
    w_part = float(setting.weight_participation) if setting else 10.0
    w_ass = float(setting.weight_assignments) if setting else 5.0
    w_imp = float(setting.weight_improvement) if setting else 10.0
    w_ach = float(setting.weight_achievements) if setting else 5.0

    total_weight = w_acad + w_att + w_beh + w_part + w_ass + w_imp + w_ach
    if total_weight <= 0: total_weight = 100.0

    s_acad = calculate_academic_score(student, month, year)
    s_att = calculate_attendance_score(student, month, year)
    s_beh = calculate_behaviour_score(student, month, year)
    s_part = calculate_participation_score(student, month, year)
    s_ass = calculate_assignment_score(student, month, year)
    s_imp = calculate_improvement_score(student, academic_year, month, year)
    s_ach = calculate_achievement_score(student, month, year)

    weighted_sum = (
        (s_acad * w_acad) +
        (s_att * w_att) +
        (s_beh * w_beh) +
        (s_part * w_part) +
        (s_ass * w_ass) +
        (s_imp * w_imp) +
        (s_ach * w_ach)
    )

    holistic_score = round(weighted_sum / total_weight, 2)

    perf_record, _ = PerformanceScore.objects.get_or_create(
        student=student,
        academic_year=academic_year,
        month=month,
        year=year
    )

    perf_record.academic_score = s_acad
    perf_record.attendance_score = s_att
    perf_record.behaviour_score = s_beh
    perf_record.participation_score = s_part
    perf_record.assignment_score = s_ass
    perf_record.improvement_score = s_imp
    perf_record.achievement_score = s_ach
    perf_record.holistic_score = holistic_score

    # Evaluate Risk Level & Recommendations
    risk_level, recs = evaluate_student_risk(student, perf_record, setting)
    perf_record.risk_level = risk_level
    perf_record.risk_recommendation = recs

    perf_record.save()
    return perf_record
