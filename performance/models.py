from django.db import models
from students.models import Student
from academics.models import AcademicYear

class PerformanceSetting(models.Model):
    academic_year = models.OneToOneField(AcademicYear, on_delete=models.CASCADE, related_name='performance_setting')
    weight_academic = models.DecimalField(max_digits=5, decimal_places=2, default=40.0, help_text="Academic weight % (e.g. 40)")
    weight_attendance = models.DecimalField(max_digits=5, decimal_places=2, default=15.0, help_text="Attendance weight % (e.g. 15)")
    weight_behaviour = models.DecimalField(max_digits=5, decimal_places=2, default=15.0, help_text="Behaviour weight % (e.g. 15)")
    weight_participation = models.DecimalField(max_digits=5, decimal_places=2, default=10.0, help_text="Participation weight % (e.g. 10)")
    weight_assignments = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="Assignments weight % (e.g. 5)")
    weight_improvement = models.DecimalField(max_digits=5, decimal_places=2, default=10.0, help_text="Improvement weight % (e.g. 10)")
    weight_achievements = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="Achievements weight % (e.g. 5)")
    min_attendance_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=75.0, help_text="Minimum attendance % required")

    def __str__(self):
        return f"Performance Settings ({self.academic_year.name})"

class PerformanceScore(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low Risk'
        MEDIUM = 'MEDIUM', 'Medium Risk'
        HIGH = 'HIGH', 'High Risk'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='performance_scores')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='performance_scores')
    month = models.IntegerField()
    year = models.IntegerField()
    
    academic_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    attendance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    behaviour_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    participation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    assignment_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    improvement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    achievement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    holistic_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    risk_recommendation = models.TextField(blank=True, null=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'academic_year', 'month', 'year']
        ordering = ['-year', '-month', '-holistic_score']

    def __str__(self):
        return f"{self.student.full_name} - {self.month}/{self.year} HPI: {self.holistic_score} ({self.risk_level})"
