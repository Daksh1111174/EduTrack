from django.db import models
from django.conf import settings
from students.models import Student

class Achievement(models.Model):
    class Category(models.TextChoices):
        ACADEMIC = 'ACADEMIC', 'Academic Excellence'
        SPORTS = 'SPORTS', 'Sports & Athletics'
        CULTURAL = 'CULTURAL', 'Cultural & Arts'
        SOCIAL = 'SOCIAL', 'Community Service'
        LEADERSHIP = 'LEADERSHIP', 'Leadership'
        OTHER = 'OTHER', 'Other Contribution'

    class Level(models.TextChoices):
        SCHOOL = 'SCHOOL', 'School Level'
        DISTRICT = 'DISTRICT', 'District Level'
        STATE = 'STATE', 'State Level'
        NATIONAL = 'NATIONAL', 'National Level'
        INTERNATIONAL = 'INTERNATIONAL', 'International Level'

    LEVEL_POINTS = {
        'SCHOOL': 5,
        'DISTRICT': 10,
        'STATE': 20,
        'NATIONAL': 30,
        'INTERNATIONAL': 40
    }

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.ACADEMIC)
    level = models.CharField(max_length=30, choices=Level.choices, default=Level.SCHOOL)
    points = models.IntegerField(default=5)
    date = models.DateField()
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.points or self.points <= 0:
            self.points = self.LEVEL_POINTS.get(self.level, 5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.title} ({self.get_level_display()})"
