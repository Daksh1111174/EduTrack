from django.db import models
from django.conf import settings
from students.models import Student, Parent
from teachers.models import Teacher

class ParentTeacherMeeting(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested (Pending Confirmation)'
        SCHEDULED = 'SCHEDULED', 'Scheduled / Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class MeetingType(models.TextChoices):
        ONLINE = 'ONLINE', 'Online Video Conference'
        IN_PERSON = 'IN_PERSON', 'In-Person (School Campus)'

    title = models.CharField(max_length=200, help_text="e.g. Term 1 Academic & Attendance Review")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='ptm_meetings')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ptm_meetings')
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='ptm_meetings')
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    meeting_type = models.CharField(max_length=20, choices=MeetingType.choices, default=MeetingType.ONLINE)
    location_or_link = models.CharField(max_length=255, default="https://meet.google.com/student360-ptm", help_text="Google Meet link or Room Number (e.g. Room 204)")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    agenda_notes = models.TextField(blank=True, null=True, help_text="Initial agenda or topics to discuss")
    summary_feedback = models.TextField(blank=True, null=True, help_text="Post-meeting summary and actionable feedback recorded by teacher")
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='requested_ptms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"PTM: {self.student.full_name} with {self.teacher.full_name} on {self.date} ({self.status})"
