from django.db import models
from django.conf import settings
from students.models import Student

class Badge(models.Model):
    class Category(models.TextChoices):
        ACADEMIC = 'ACADEMIC', 'Academic Excellence'
        ATTENDANCE = 'ATTENDANCE', 'Attendance Streak'
        BEHAVIOUR = 'BEHAVIOUR', 'Behaviour & Conduct'
        ASSIGNMENT = 'ASSIGNMENT', 'Homework & Assignments'
        OVERALL = 'OVERALL', 'Holistic Champion'

    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ACADEMIC)
    icon = models.CharField(max_length=50, default="fa-award", help_text="FontAwesome icon class (e.g. fa-fire, fa-crown, fa-bolt)")
    xp_reward = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (+{self.xp_reward} XP)"

class StudentBadge(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_students')
    earned_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')
        ordering = ['-earned_date']

    def __str__(self):
        return f"{self.student.full_name} earned {self.badge.title}"

class StudentGamificationProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='gamification_profile')
    total_xp = models.IntegerField(default=0)
    current_attendance_streak = models.IntegerField(default=0)
    current_homework_streak = models.IntegerField(default=0)

    class Meta:
        ordering = ['-total_xp']

    @property
    def level(self):
        return (self.total_xp // 500) + 1

    @property
    def xp_in_current_level(self):
        return self.total_xp % 500

    @property
    def xp_needed_for_next_level(self):
        return 500 - (self.total_xp % 500)

    @property
    def level_progress_percentage(self):
        return int((self.xp_in_current_level / 500.0) * 100)

    @property
    def rank_title(self):
        lvl = self.level
        if lvl >= 10: return "Academic Legend 👑"
        elif lvl >= 7: return "Master Scholar 🌟"
        elif lvl >= 5: return "Honor Roll Elite ⚡"
        elif lvl >= 3: return "Rising Scholar 🚀"
        else: return "Novice Apprentice 🌱"

    def __str__(self):
        return f"{self.student.full_name} - Level {self.level} ({self.total_xp} XP)"
