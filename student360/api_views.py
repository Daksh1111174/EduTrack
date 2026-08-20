from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes

from accounts.models import User
from academics.models import Class, Division, Subject, Exam, Mark
from students.models import Student
from teachers.models import Teacher
from attendance.models import Attendance
from behaviour.models import BehaviourRecord
from assignments.models import Assignment, AssignmentSubmission
from participation.models import Participation
from achievements.models import Achievement
from remarks.models import TeacherRemark
from performance.models import PerformanceScore
from awards.models import StudentAward

from student360.serializers import (
    UserSerializer, ClassSerializer, DivisionSerializer, SubjectSerializer,
    StudentSerializer, TeacherSerializer, ExamSerializer, MarkSerializer,
    AttendanceSerializer, BehaviourRecordSerializer, AssignmentSerializer,
    AssignmentSubmissionSerializer, ParticipationSerializer, AchievementSerializer,
    TeacherRemarkSerializer, PerformanceScoreSerializer, StudentAwardSerializer
)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['class_obj', 'division_obj', 'gender']
    search_fields = ['first_name', 'last_name', 'student_id']

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated]

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

class MarkViewSet(viewsets.ModelViewSet):
    queryset = Mark.objects.all()
    serializer_class = MarkSerializer
    permission_classes = [permissions.IsAuthenticated]

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

class BehaviourViewSet(viewsets.ModelViewSet):
    queryset = BehaviourRecord.objects.all()
    serializer_class = BehaviourRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class ParticipationViewSet(viewsets.ModelViewSet):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer
    permission_classes = [permissions.IsAuthenticated]

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

class TeacherRemarkViewSet(viewsets.ModelViewSet):
    queryset = TeacherRemark.objects.all()
    serializer_class = TeacherRemarkSerializer
    permission_classes = [permissions.IsAuthenticated]

class PerformanceScoreViewSet(viewsets.ModelViewSet):
    queryset = PerformanceScore.objects.all()
    serializer_class = PerformanceScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

class StudentAwardViewSet(viewsets.ModelViewSet):
    queryset = StudentAward.objects.all()
    serializer_class = StudentAwardSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_api_summary(request):
    """Returns aggregated performance metrics summary for dashboard widgets."""
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = Class.objects.count()
    at_risk_count = PerformanceScore.objects.filter(risk_level='HIGH').count()

    scores = PerformanceScore.objects.all()
    avg_hpi = round(sum(s.holistic_score for s in scores) / len(scores), 1) if scores.exists() else 75.0
    avg_att = round(sum(s.attendance_score for s in scores) / len(scores), 1) if scores.exists() else 88.0

    return Response({
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'at_risk_students': at_risk_count,
        'average_hpi': float(avg_hpi),
        'average_attendance': float(avg_att)
    })
