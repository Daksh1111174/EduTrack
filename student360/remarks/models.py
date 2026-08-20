from django.db import models
from django.conf import settings
from students.models import Student

class TeacherRemark(models.Model):
    class Category(models.TextChoices):
        ACADEMIC = 'ACADEMIC', 'Academic'
        BEHAVIOUR = 'BEHAVIOUR', 'Behaviour'
        ATTENDANCE = 'ATTENDANCE', 'Attendance'
        PARTICIPATION = 'PARTICIPATION', 'Participation'
        GENERAL = 'GENERAL', 'General Observation'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='teacher_remarks')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_remarks')
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)
    remark = models.TextField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Remark for {self.student.full_name} by {self.teacher.username} ({self.category})"
