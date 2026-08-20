from django.utils import timezone
from academics.models import AcademicYear, Class, Division
from students.models import Student
from performance.models import PerformanceScore, PerformanceSetting
from performance.services import calculate_student_hpi
from awards.models import StudentAward
from notifications.services import send_smart_notification

def generate_student_of_the_month_suggestions(academic_year=None, month=None, year=None):
    """
    Ranks eligible students per class/division and automatically decides and approves Student of the Month
    winners based on highest Holistic Performance Index (HPI). Sends instant smart notifications to Student and Parents.
    """
    now = timezone.now()
    if not month: month = now.month
    if not year: year = now.year

    if not academic_year:
        academic_year = AcademicYear.objects.filter(is_active=True).first()

    if not academic_year:
        return []

    setting = PerformanceSetting.objects.filter(academic_year=academic_year).first()
    min_att = float(setting.min_attendance_threshold) if setting else 75.0

    created_awards = []
    classes = Class.objects.all()
    divisions = Division.objects.all()

    for cls in classes:
        for div in divisions:
            students = Student.objects.filter(class_obj=cls, division_obj=div, academic_year=academic_year)
            if not students.exists():
                continue

            eligible_candidates = []
            for student in students:
                perf_score = PerformanceScore.objects.filter(
                    student=student, academic_year=academic_year, month=month, year=year
                ).first()

                if not perf_score:
                    perf_score = calculate_student_hpi(student, academic_year, month, year)

                if float(perf_score.attendance_score) < min_att:
                    continue
                if float(perf_score.behaviour_score) < 60.0:
                    continue

                eligible_candidates.append((student, perf_score))

            if not eligible_candidates:
                continue

            eligible_candidates.sort(key=lambda x: x[1].holistic_score, reverse=True)
            top_student, top_perf = eligible_candidates[0]

            existing = StudentAward.objects.filter(
                student__class_obj=cls,
                student__division_obj=div,
                academic_year=academic_year,
                month=month,
                year=year,
                award_type=StudentAward.AwardType.STUDENT_OF_THE_MONTH
            ).first()

            if not existing:
                reason_text = (
                    f"Auto-decided winner based on highest Holistic Performance Index ({top_perf.holistic_score:.1f}/100) in {cls.name}-{div.name}. "
                    f"Academic: {top_perf.academic_score}%, Attendance: {top_perf.attendance_score}%, "
                    f"Behaviour: {top_perf.behaviour_score}%."
                )
                award = StudentAward.objects.create(
                    student=top_student,
                    academic_year=academic_year,
                    month=month,
                    year=year,
                    award_type=StudentAward.AwardType.STUDENT_OF_THE_MONTH,
                    status=StudentAward.Status.APPROVED,
                    reason=reason_text
                )
                created_awards.append(award)

                # Send Notification to Student & Parents
                send_smart_notification(
                    top_student,
                    title="🏆 Congratulations! Student of the Month Awarded!",
                    message=f"Congratulations! {top_student.full_name} has been awarded Student of the Month for {month}/{year}!",
                    link='/dashboard/'
                )

            elif existing.status == StudentAward.Status.SUGGESTED:
                existing.status = StudentAward.Status.APPROVED
                existing.save()

    return created_awards
