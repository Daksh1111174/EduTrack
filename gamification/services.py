from gamification.models import Badge, StudentBadge, StudentGamificationProfile
from performance.models import PerformanceScore
from attendance.models import Attendance
from assignments.models import AssignmentSubmission
from achievements.models import Achievement

DEFAULT_BADGES = [
    {
        'title': 'Perfect Attendance Master',
        'description': 'Maintained 95%+ attendance compliance across the term.',
        'category': Badge.Category.ATTENDANCE,
        'icon': 'fa-fire',
        'xp_reward': 150
    },
    {
        'title': 'Academic Scholar',
        'description': 'Achieved 90%+ average across all examination subjects.',
        'category': Badge.Category.ACADEMIC,
        'icon': 'fa-graduation-cap',
        'xp_reward': 250
    },
    {
        'title': 'Classroom Role Model',
        'description': 'Received 90%+ top rating in discipline & conduct ratings.',
        'category': Badge.Category.BEHAVIOUR,
        'icon': 'fa-star',
        'xp_reward': 200
    },
    {
        'title': 'Homework Master',
        'description': 'Completed 85%+ assignments on time with high quality.',
        'category': Badge.Category.ASSIGNMENT,
        'icon': 'fa-bolt',
        'xp_reward': 150
    },
    {
        'title': 'Student360 Champion',
        'description': 'Achieved an overall Holistic Performance Index (HPI) above 85.0.',
        'category': Badge.Category.OVERALL,
        'icon': 'fa-crown',
        'xp_reward': 500
    },
    {
        'title': 'Multi-Talented Star',
        'description': 'Accumulated 3 or more co-curricular achievements and awards.',
        'category': Badge.Category.ACADEMIC,
        'icon': 'fa-medal',
        'xp_reward': 200
    }
]

def init_default_badges():
    """Initializes standard achievement badges if not present."""
    for b_data in DEFAULT_BADGES:
        Badge.objects.get_or_create(
            title=b_data['title'],
            defaults=b_data
        )

def evaluate_and_award_student_badges(student):
    """
    Evaluates student's live performance data and unlocks eligible achievement badges,
    grants XP, and updates streaks and levels. Uses get_or_create to prevent IntegrityErrors.
    """
    if not student:
        return None

    init_default_badges()

    profile, _ = StudentGamificationProfile.objects.get_or_create(student=student)
    perf = PerformanceScore.objects.filter(student=student).first()

    # Calculate streaks
    att_present_count = Attendance.objects.filter(student=student, status=Attendance.Status.PRESENT).count()
    profile.current_attendance_streak = att_present_count

    sub_count = AssignmentSubmission.objects.filter(student=student).count()
    profile.current_homework_streak = sub_count
    profile.save()

    earned_badges_ids = set(StudentBadge.objects.filter(student=student).values_list('badge_id', flat=True))

    new_xp = 0

    if perf:
        # 1. Attendance Badge
        if float(perf.attendance_score) >= 90.0:
            badge = Badge.objects.filter(title='Perfect Attendance Master').first()
            if badge and badge.id not in earned_badges_ids:
                sb, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
                if created:
                    earned_badges_ids.add(badge.id)
                    new_xp += badge.xp_reward

        # 2. Academic Badge
        if float(perf.academic_score) >= 85.0:
            badge = Badge.objects.filter(title='Academic Scholar').first()
            if badge and badge.id not in earned_badges_ids:
                sb, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
                if created:
                    earned_badges_ids.add(badge.id)
                    new_xp += badge.xp_reward

        # 3. Behaviour Badge
        if float(perf.behaviour_score) >= 85.0:
            badge = Badge.objects.filter(title='Classroom Role Model').first()
            if badge and badge.id not in earned_badges_ids:
                sb, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
                if created:
                    earned_badges_ids.add(badge.id)
                    new_xp += badge.xp_reward

        # 4. Homework Badge
        if float(perf.assignment_score) >= 80.0:
            badge = Badge.objects.filter(title='Homework Master').first()
            if badge and badge.id not in earned_badges_ids:
                sb, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
                if created:
                    earned_badges_ids.add(badge.id)
                    new_xp += badge.xp_reward

        # 5. HPI Champion Badge
        if float(perf.holistic_score) >= 80.0:
            badge = Badge.objects.filter(title='Student360 Champion').first()
            if badge and badge.id not in earned_badges_ids:
                sb, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
                if created:
                    earned_badges_ids.add(badge.id)
                    new_xp += badge.xp_reward

    # 6. Achievements Badge
    if Achievement.objects.filter(student=student).count() >= 1:
        badge = Badge.objects.filter(title='Multi-Talented Star').first()
        if badge and badge.id not in earned_badges_ids:
            sb, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
            if created:
                earned_badges_ids.add(badge.id)
                new_xp += badge.xp_reward

    if new_xp > 0:
        profile.total_xp += new_xp
        profile.save()

    # Recalculate total XP from all earned badges to stay synchronized
    total_badge_xp = sum(sb.badge.xp_reward for sb in StudentBadge.objects.filter(student=student).select_related('badge'))
    profile.total_xp = max(profile.total_xp, total_badge_xp)
    profile.save()

    return profile
