from django.db import models
from django.conf import settings
from students.models import Student
from academics.models import Class, Division

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        LEAVE = 'LEAVE', 'Leave'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_records')
    division_obj = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student__roll_number']

    def __str__(self):
        return f"{self.student.full_name} - {self.date}: {self.status}"
