import random
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

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
from performance.services import calculate_student_hpi
from awards.services import generate_student_of_the_month_suggestions

FIRST_NAMES = [
    "Aarav", "Riya", "Dev", "Anaya", "Vihaan", "Isha", "Kabir", "Diya", "Reyansh", "Myra",
    "Arjun", "Aditi", "Sai", "Pari", "Krishna", "Ananya", "Ishaan", "Avani", "Rohan", "Saniya",
    "Vivaan", "Kavya", "Aditya", "Tara", "Yash", "Meera", "Ayaan", "Shruti", "Dhruv", "Prisha",
    "Siddharth", "Tanvi", "Nikhil", "Neha", "Karan", "Pooja", "Rahul", "Sneha", "Amit", "Ritu"
]

LAST_NAMES = [
    "Shah", "Patel", "Mehta", "Sharma", "Verma", "Joshi", "Gupta", "Desai", "Rao", "Nair",
    "Malhotra", "Kapoor", "Bhat", "Kulkarni", "Singhal", "Chopra", "Reddy", "Saxena", "Trivedi", "Iyer"
]

SUBJECTS_DATA = [
    ("Mathematics", "MATH101"),
    ("Physics", "PHYS101"),
    ("Chemistry", "CHEM101"),
    ("Biology", "BIOL101"),
    ("English Literature", "ENG101"),
    ("History & Civics", "HIST101"),
    ("Computer Science", "CS101"),
    ("Economics", "ECON101"),
    ("Geography", "GEOG101"),
    ("Art & Design", "ART101")
]

class Command(BaseCommand):
    help = "Seeds database with 1 Admin, 12 Teachers, 5 Classes, 3 Divisions, 10 Subjects, 120 Students, Marks, Attendance, Behaviour, Achievements, and HPI Scores."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting EduTrack database seed process...")

        Attendance.objects.all().delete()
        Mark.objects.all().delete()
        Exam.objects.all().delete()
        BehaviourRecord.objects.all().delete()
        Participation.objects.all().delete()
        Achievement.objects.all().delete()
        TeacherRemark.objects.all().delete()
        PerformanceScore.objects.all().delete()
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        User.objects.filter(role__in=[User.Role.STUDENT, User.Role.TEACHER, User.Role.PARENT]).delete()

        # 1. Academic Year
        acad_year, _ = AcademicYear.objects.get_or_create(
            name="2025-2026",
            defaults={
                'start_date': datetime.date(2025, 6, 1),
                'end_date': datetime.date(2026, 4, 30),
                'is_active': True
            }
        )
        PerformanceSetting.objects.get_or_create(academic_year=acad_year)

        # 2. Admin User
        admin_user, admin_created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'EduTrack',
                'last_name': 'Administrator',
                'email': 'admin@edutrack.edu',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if admin_created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write("Created Admin user: admin / admin123")

        # 3. Classes & Divisions
        classes = []
        for c_name in ["Class 8", "Class 9", "Class 10", "Class 11", "Class 12"]:
            c_obj, _ = Class.objects.get_or_create(name=c_name, defaults={'code': c_name.replace(" ", "").upper()})
            classes.append(c_obj)

        divisions = []
        for d_name in ["A", "B", "C"]:
            d_obj, _ = Division.objects.get_or_create(name=d_name)
            divisions.append(d_obj)

        # 4. Subjects
        subjects = []
        for s_name, s_code in SUBJECTS_DATA:
            s_obj, _ = Subject.objects.get_or_create(name=s_name, defaults={'code': s_code})
            subjects.append(s_obj)

        # 5. Create 12 Teachers
        teachers = []
        for i in range(1, 13):
            username = f"teacher{i}"
            t_user, u_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': random.choice(FIRST_NAMES),
                    'last_name': random.choice(LAST_NAMES),
                    'email': f"teacher{i}@edutrack.edu",
                    'role': User.Role.TEACHER
                }
            )
            if u_created:
                t_user.set_password('teacher123')
                t_user.save()

            teacher, _ = Teacher.objects.get_or_create(
                employee_id=f"EMP200{i}",
                defaults={
                    'user': t_user,
                    'first_name': t_user.first_name,
                    'last_name': t_user.last_name,
                    'email': t_user.email,
                    'department': 'Academics',
                    'designation': 'Senior Faculty'
                }
            )
            teachers.append(teacher)
        self.stdout.write(f"Created {len(teachers)} Teachers (teacher1..teacher12 / teacher123)")

        # Map Teachers to Subjects & Classes
        for idx, cls in enumerate(classes):
            for div in divisions:
                for subj in subjects[:4]:
                    t_assigned = teachers[(idx + subjects.index(subj)) % len(teachers)]
                    TeacherSubjectAssignment.objects.get_or_create(
                        teacher=t_assigned,
                        class_obj=cls,
                        division_obj=div,
                        subject=subj,
                        academic_year=acad_year
                    )

        # 6. Create 120 Students
        students = []
        stu_counter = 1001
        for cls in classes:
            for div in divisions:
                for roll in range(1, 9):
                    stu_id = f"STU{stu_counter}"
                    fn = random.choice(FIRST_NAMES)
                    ln = random.choice(LAST_NAMES)
                    u_name = f"student{stu_counter - 1000}"

                    s_user, su_created = User.objects.get_or_create(
                        username=u_name,
                        defaults={
                            'first_name': fn,
                            'last_name': ln,
                            'email': f"{u_name}@edutrack.edu",
                            'role': User.Role.STUDENT
                        }
                    )
                    if su_created:
                        s_user.set_password('student123')
                        s_user.save()

                    student, _ = Student.objects.get_or_create(
                        student_id=stu_id,
                        defaults={
                            'user': s_user,
                            'first_name': fn,
                            'last_name': ln,
                            'email': s_user.email,
                            'gender': random.choice(['MALE', 'FEMALE']),
                            'class_obj': cls,
                            'division_obj': div,
                            'roll_number': roll,
                            'academic_year': acad_year
                        }
                    )
                    students.append(student)
                    stu_counter += 1

        self.stdout.write(f"Created {len(students)} Students (student1..student{len(students)} / student123)")

        # 7. Create Parent Accounts
        for i in range(1, 25):
            p_user, pu_created = User.objects.get_or_create(
                username=f"parent{i}",
                defaults={
                    'first_name': random.choice(FIRST_NAMES),
                    'last_name': random.choice(LAST_NAMES),
                    'email': f"parent{i}@edutrack.edu",
                    'role': User.Role.PARENT
                }
            )
            if pu_created:
                p_user.set_password('parent123')
                p_user.save()

            parent_obj, _ = Parent.objects.get_or_create(
                user=p_user,
                defaults={'relationship': 'FATHER'}
            )
            parent_obj.students.set(random.sample(students, 2))

        # 8. Create Exams
        exams = []
        for cls in classes:
            for div in divisions:
                for subj in subjects[:5]:
                    exam_obj = Exam.objects.create(
                        name="Unit Test 1",
                        subject=subj,
                        class_obj=cls,
                        division_obj=div,
                        academic_year=acad_year,
                        exam_type=Exam.ExamType.UNIT_TEST,
                        max_marks=Decimal("50.00"),
                        date=datetime.date(2025, 9, 15)
                    )
                    exams.append(exam_obj)

                    midterm_obj = Exam.objects.create(
                        name="Midterm Examination",
                        subject=subj,
                        class_obj=cls,
                        division_obj=div,
                        academic_year=acad_year,
                        exam_type=Exam.ExamType.MIDTERM,
                        max_marks=Decimal("100.00"),
                        date=datetime.date(2025, 11, 20)
                    )
                    exams.append(midterm_obj)

        # 9. Create Marks in Bulk
        marks_to_create = []
        for student in students:
            stu_exams = [e for e in exams if e.class_obj == student.class_obj and e.division_obj == student.division_obj]
            base_pct = random.uniform(45.0, 95.0)

            for exam in stu_exams:
                max_m = float(exam.max_marks)
                pct = max(20.0, min(100.0, base_pct + random.uniform(-10.0, 10.0)))
                obtained_val = Decimal(str(round((pct / 100.0) * max_m, 2)))
                marks_to_create.append(Mark(
                    student=student,
                    exam=exam,
                    marks_obtained=obtained_val,
                    entered_by=teachers[0].user
                ))
        Mark.objects.bulk_create(marks_to_create)

        # 10. Create Attendance Logs in Bulk (15 days history)
        attendance_to_create = []
        today = datetime.date.today()
        for day_offset in range(1, 16):
            att_date = today - datetime.timedelta(days=day_offset)
            if att_date.weekday() in [5, 6]:
                continue

            for student in students:
                rnd = random.random()
                st = Attendance.Status.PRESENT if rnd < 0.88 else (Attendance.Status.ABSENT if rnd < 0.94 else Attendance.Status.LATE)
                attendance_to_create.append(Attendance(
                    student=student,
                    date=att_date,
                    class_obj=student.class_obj,
                    division_obj=student.division_obj,
                    status=st,
                    marked_by=teachers[0].user
                ))
        Attendance.objects.bulk_create(attendance_to_create)

        # 11. Create Behaviour & Participation Records in Bulk
        beh_to_create = []
        part_to_create = []
        for student in students:
            beh_to_create.append(BehaviourRecord(
                student=student,
                date=today - datetime.timedelta(days=3),
                discipline=random.randint(2, 5), respect=random.randint(3, 5),
                responsibility=random.randint(2, 5), cooperation=random.randint(3, 5),
                punctuality=random.randint(2, 5), classroom_conduct=random.randint(3, 5),
                leadership=random.randint(2, 5), teamwork=random.randint(3, 5),
                recorded_by=teachers[0].user
            ))
            part_to_create.append(Participation(
                student=student,
                date=today - datetime.timedelta(days=3),
                class_participation=random.randint(2, 5), question_asking=random.randint(2, 5),
                presentation=random.randint(2, 5), group_activities=random.randint(3, 5),
                leadership=random.randint(2, 5), extracurricular=random.randint(2, 5),
                recorded_by=teachers[0].user
            ))
        BehaviourRecord.objects.bulk_create(beh_to_create)
        Participation.objects.bulk_create(part_to_create)

        # 12. Achievements & Remarks
        sample_achievements = [
            ("Science Fair Winner", "1st place in Inter-School Science Exhibition", "ACADEMIC", "DISTRICT"),
            ("Math Olympiad Gold", "Gold Medal in State Mathematics Competition", "ACADEMIC", "STATE"),
            ("Inter-School Football Captain", "Led school team to victory", "SPORTS", "DISTRICT"),
            ("National Debate Finalist", "Represented school in National Debate", "CULTURAL", "NATIONAL"),
        ]
        ach_to_create = []
        for student in random.sample(students, 40):
            title, desc, cat, lvl = random.choice(sample_achievements)
            ach_to_create.append(Achievement(
                student=student, title=title, description=desc, category=cat, level=lvl,
                date=today - datetime.timedelta(days=10), awarded_by=admin_user
            ))
        Achievement.objects.bulk_create(ach_to_create)

        rem_to_create = []
        for student in random.sample(students, 50):
            rem_to_create.append(TeacherRemark(
                student=student, teacher=teachers[0].user, category='GENERAL',
                remark="Demonstrates excellent curiosity and actively contributes during class discussions."
            ))
        TeacherRemark.objects.bulk_create(rem_to_create)

        # 13. Calculate HPI Scores & Student of the Month Nominations
        self.stdout.write("Calculating Holistic Performance Index (HPI) for all students...")
        for student in students:
            calculate_student_hpi(student, acad_year)

        self.stdout.write("Running Student of the Month ranking algorithm...")
        generate_student_of_the_month_suggestions(acad_year)

        self.stdout.write(self.style.SUCCESS("Database successfully seeded with 120 Students and 12 Teachers!"))
