from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. 2025-2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Class(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Class 10")
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['name']

    def __str__(self):
        return self.name

class Division(models.Model):
    name = models.CharField(max_length=10, unique=True, help_text="e.g. A, B, C")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Exam(models.Model):
    class ExamType(models.TextChoices):
        UNIT_TEST = 'UNIT_TEST', 'Unit Test'
        MIDTERM = 'MIDTERM', 'Midterm Exam'
        FINAL = 'FINAL', 'Final Exam'
        QUIZ = 'QUIZ', 'Quiz'

    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=30, choices=ExamType.choices, default=ExamType.UNIT_TEST)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='exams')
    division_obj = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exams')

    def __str__(self):
        return f"{self.name} - {self.subject.name} ({self.class_obj.name})"

class Mark(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='marks')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'exam']

    def clean(self):
        if self.marks_obtained is not None and self.exam is not None:
            if self.marks_obtained > self.exam.max_marks:
                raise ValidationError({'marks_obtained': f"Marks obtained ({self.marks_obtained}) cannot exceed maximum marks ({self.exam.max_marks})."})
            if self.marks_obtained < 0:
                raise ValidationError({'marks_obtained': "Marks obtained cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def percentage(self):
        if self.exam and self.exam.max_marks > 0:
            return round((float(self.marks_obtained) / float(self.exam.max_marks)) * 100, 2)
        return 0.0

    @property
    def grade(self):
        pct = self.percentage
        if pct >= 90: return 'A+'
        if pct >= 80: return 'A'
        if pct >= 70: return 'B'
        if pct >= 60: return 'C'
        if pct >= 50: return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student} - {self.exam.subject.name}: {self.marks_obtained}/{self.exam.max_marks}"
