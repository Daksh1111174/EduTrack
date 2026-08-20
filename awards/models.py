from django.db import models
from django.conf import settings
from students.models import Student
from academics.models import AcademicYear

class StudentAward(models.Model):
    class AwardType(models.TextChoices):
        STUDENT_OF_THE_MONTH = 'STUDENT_OF_THE_MONTH', 'Student of the Month'
        MOST_IMPROVED = 'MOST_IMPROVED', 'Most Improved Student'
        ACADEMIC_EXCELLENCE = 'ACADEMIC_EXCELLENCE', 'Academic Excellence Award'
        BEST_ATTENDANCE = 'BEST_ATTENDANCE', 'Best Attendance Award'
        BEST_BEHAVIOUR = 'BEST_BEHAVIOUR', 'Best Behaviour Award'
        OUTSTANDING_PARTICIPATION = 'OUTSTANDING_PARTICIPATION', 'Outstanding Participation Award'
        ACHIEVEMENT_AWARD = 'ACHIEVEMENT_AWARD', 'Special Achievement Award'

    class Status(models.TextChoices):
        SUGGESTED = 'SUGGESTED', 'Suggested (Pending Approval)'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='awards')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='awards')
    month = models.IntegerField()
    year = models.IntegerField()
    award_type = models.CharField(max_length=40, choices=AwardType.choices, default=AwardType.STUDENT_OF_THE_MONTH)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUGGESTED)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True, null=True)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'academic_year', 'month', 'year', 'award_type']
        ordering = ['-year', '-month', '-awarded_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.get_award_type_display()} ({self.month}/{self.year}) [{self.status}]"
