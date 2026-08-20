from rest_framework import serializers
from accounts.models import User
from academics.models import AcademicYear, Class, Division, Subject, Exam, Mark
from students.models import Student, Parent
from teachers.models import Teacher, TeacherSubjectAssignment
from attendance.models import Attendance
from behaviour.models import BehaviourRecord
from assignments.models import Assignment, AssignmentSubmission
from participation.models import Participation
from achievements.models import Achievement
from remarks.models import TeacherRemark
from performance.models import PerformanceSetting, PerformanceScore
from awards.models import StudentAward
from notifications.models import Notification

class UserSerializer(serializers.ModelResourceSerializer if hasattr(serializers, 'ModelResourceSerializer') else serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone_number']

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'

class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    division_name = serializers.CharField(source='division_obj.name', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Student
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Teacher
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Exam
        fields = '__all__'

class MarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_name = serializers.CharField(source='exam.subject.name', read_only=True)
    percentage = serializers.FloatField(read_only=True)
    grade = serializers.CharField(read_only=True)

    class Meta:
        model = Mark
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'

class BehaviourRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    percentage_score = serializers.FloatField(read_only=True)

    class Meta:
        model = BehaviourRecord
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Assignment
        fields = '__all__'

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = '__all__'

class ParticipationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Participation
        fields = '__all__'

class AchievementSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Achievement
        fields = '__all__'

class TeacherRemarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)

    class Meta:
        model = TeacherRemark
        fields = '__all__'

class PerformanceScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = PerformanceScore
        fields = '__all__'

class StudentAwardSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = StudentAward
        fields = '__all__'
