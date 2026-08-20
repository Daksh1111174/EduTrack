from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from students.models import Student
from academics.models import Class, Division, Subject

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assignments')
    division_obj = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    due_date = models.DateField()
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.subject.name} - {self.class_obj.name} {self.division_obj.name})"

class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted On-Time'
        LATE = 'LATE', 'Late Submission'
        MISSING = 'MISSING', 'Missing'
        GRADED = 'GRADED', 'Graded'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    submission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.MISSING)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['assignment', 'student']

    @property
    def percentage(self):
        if self.marks_obtained is not None and self.assignment.max_marks > 0:
            return round((float(self.marks_obtained) / float(self.assignment.max_marks)) * 100, 2)
        return 0.0

    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}: {self.status}"
