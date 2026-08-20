from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from students.models import Student

class Participation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='participation_records')
    date = models.DateField()
    class_participation = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    question_asking = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    presentation = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    group_activities = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    leadership = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    extracurricular = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    @property
    def average_rating(self):
        ratings = [
            self.class_participation, self.question_asking, self.presentation,
            self.group_activities, self.leadership, self.extracurricular
        ]
        return round(sum(ratings) / len(ratings), 2)

    @property
    def percentage_score(self):
        return round((self.average_rating / 5.0) * 100, 2)

    def __str__(self):
        return f"{self.student.full_name} Participation ({self.date}): {self.average_rating}/5.0"
