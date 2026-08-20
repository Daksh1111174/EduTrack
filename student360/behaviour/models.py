from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from students.models import Student

class BehaviourRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behaviour_records')
    date = models.DateField()
    discipline = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    respect = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    responsibility = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    cooperation = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    punctuality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    classroom_conduct = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    leadership = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    @property
    def average_rating(self):
        ratings = [
            self.discipline, self.respect, self.responsibility, self.cooperation,
            self.punctuality, self.classroom_conduct, self.leadership, self.teamwork
        ]
        return round(sum(ratings) / len(ratings), 2)

    @property
    def percentage_score(self):
        return round((self.average_rating / 5.0) * 100, 2)

    def __str__(self):
        return f"{self.student.full_name} Behaviour ({self.date}): {self.average_rating}/5.0"
