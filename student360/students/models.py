from django.db import models
from django.conf import settings
from academics.models import Class, Division, AcademicYear

class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')
    division_obj = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='students')
    roll_number = models.IntegerField()
    admission_date = models.DateField(auto_now_add=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, related_name='students')
    profile_photo = models.ImageField(upload_to='students/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_obj', 'division_obj', 'roll_number']
        unique_together = ['class_obj', 'division_obj', 'roll_number']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} ({self.student_id} - {self.class_obj.name} {self.division_obj.name})"

class Parent(models.Model):
    class Relationship(models.TextChoices):
        FATHER = 'FATHER', 'Father'
        MOTHER = 'MOTHER', 'Mother'
        GUARDIAN = 'GUARDIAN', 'Guardian'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    relationship = models.CharField(max_length=20, choices=Relationship.choices, default=Relationship.FATHER)
    students = models.ManyToManyField(Student, related_name='parents')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.relationship})"
