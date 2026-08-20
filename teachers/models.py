from django.db import models
from django.conf import settings
from academics.models import Class, Division, Subject, AcademicYear

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, default='General')
    designation = models.CharField(max_length=100, default='Senior Teacher')
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"

class TeacherSubjectAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='teacher_assignments')
    division_obj = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='teacher_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teacher_assignments')

    class Meta:
        unique_together = ['teacher', 'class_obj', 'division_obj', 'subject', 'academic_year']

    def __str__(self):
        return f"{self.teacher.full_name} -> {self.class_obj.name} {self.division_obj.name} ({self.subject.name})"
