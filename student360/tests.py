import datetime
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse

from accounts.models import User
from academics.models import AcademicYear, Class, Division, Subject, Exam, Mark
from students.models import Student
from teachers.models import Teacher
from attendance.models import Attendance
from behaviour.models import BehaviourRecord
from performance.models import PerformanceSetting, PerformanceScore
from performance.services import calculate_student_hpi
from performance.risk_engine import evaluate_student_risk
from awards.models import StudentAward
from awards.services import generate_student_of_the_month_suggestions

class Student360TestSuite(TestCase):
    def setUp(self):
        # Academic Year & Setting
        self.year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=datetime.date(2025, 6, 1),
            end_date=datetime.date(2026, 4, 30),
            is_active=True
        )
        self.setting = PerformanceSetting.objects.create(academic_year=self.year)

        # Users
        self.admin_user = User.objects.create_superuser(username='admin_test', email='admin@test.com', password='password123', role=User.Role.ADMIN)
        self.teacher_user = User.objects.create_user(username='teacher_test', email='teacher@test.com', password='password123', role=User.Role.TEACHER)
        self.student_user = User.objects.create_user(username='student_test', email='student@test.com', password='password123', role=User.Role.STUDENT)

        # Class, Division, Subject
        self.cls = Class.objects.create(name="Class 10", code="C10")
        self.div = Division.objects.create(name="A")
        self.subj = Subject.objects.create(name="Mathematics", code="MATH10")

        # Teacher & Student
        self.teacher = Teacher.objects.create(user=self.teacher_user, employee_id="EMP999", first_name="John", last_name="Doe", email="teacher@test.com")
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="STU999",
            first_name="Aarav",
            last_name="Shah",
            class_obj=self.cls,
            division_obj=self.div,
            roll_number=1,
            academic_year=self.year
        )

        # Exam
        self.exam = Exam.objects.create(
            name="Unit Test 1",
            subject=self.subj,
            class_obj=self.cls,
            division_obj=self.div,
            max_marks=50.0,
            date=datetime.date(2025, 9, 1),
            academic_year=self.year
        )

    def test_user_role_properties(self):
        """Test custom user role properties."""
        self.assertTrue(self.admin_user.is_admin)
        self.assertTrue(self.teacher_user.is_teacher)
        self.assertTrue(self.student_user.is_student)

    def test_mark_validation_exceed_max_marks(self):
        """Test that entering marks higher than max_marks raises ValidationError."""
        invalid_mark = Mark(
            student=self.student,
            exam=self.exam,
            marks_obtained=60.0,  # Max is 50.0
            entered_by=self.teacher_user
        )
        with self.assertRaises(ValidationError):
            invalid_mark.full_clean()

    def test_valid_mark_creation_and_percentage(self):
        """Test valid mark creation and percentage calculation."""
        mark = Mark.objects.create(
            student=self.student,
            exam=self.exam,
            marks_obtained=40.0,
            entered_by=self.teacher_user
        )
        self.assertEqual(mark.percentage, 80.0)
        self.assertEqual(mark.grade, 'A')

    def test_behaviour_record_score_scaling(self):
        """Test 8-dimension behaviour score average and 100% scaling."""
        b_rec = BehaviourRecord.objects.create(
            student=self.student,
            date=datetime.date.today(),
            discipline=5, respect=5, responsibility=4, cooperation=4,
            punctuality=5, classroom_conduct=4, leadership=4, teamwork=5
        )
        self.assertEqual(b_rec.average_rating, 4.5)
        self.assertEqual(b_rec.percentage_score, 90.0)

    def test_hpi_calculation_engine(self):
        """Test Holistic Performance Index (HPI) score calculation."""
        Mark.objects.create(student=self.student, exam=self.exam, marks_obtained=45.0, entered_by=self.teacher_user)
        Attendance.objects.create(student=self.student, date=datetime.date.today(), class_obj=self.cls, division_obj=self.div, status=Attendance.Status.PRESENT)

        perf_score = calculate_student_hpi(self.student, self.year)
        self.assertGreater(perf_score.holistic_score, 0.0)
        self.assertEqual(perf_score.risk_level, PerformanceScore.RiskLevel.LOW)

    def test_at_risk_detection_thresholds(self):
        """Test high risk classification for low attendance and marks."""
        perf_score = PerformanceScore.objects.create(
            student=self.student,
            academic_year=self.year,
            month=9, year=2025,
            academic_score=40.0,
            attendance_score=50.0,
            behaviour_score=60.0,
            holistic_score=48.0
        )
        risk, rec = evaluate_student_risk(self.student, perf_score, self.setting)
        self.assertEqual(risk, 'HIGH')

    def test_student_of_the_month_algorithm(self):
        """Test Student of the Month selection per Class/Division."""
        Mark.objects.create(student=self.student, exam=self.exam, marks_obtained=48.0, entered_by=self.teacher_user)
        Attendance.objects.create(student=self.student, date=datetime.date.today(), class_obj=self.cls, division_obj=self.div, status=Attendance.Status.PRESENT)
        calculate_student_hpi(self.student, self.year)

        awards = generate_student_of_the_month_suggestions(self.year)
        self.assertTrue(len(awards) >= 1)
        self.assertEqual(awards[0].student, self.student)
