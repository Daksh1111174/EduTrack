import csv
import io
from django.db import transaction
from django.contrib.auth import get_user_model
from academics.models import Class, Division, AcademicYear, Subject, Exam, Mark
from students.models import Student
from teachers.models import Teacher
from attendance.models import Attendance
from achievements.models import Achievement

User = get_user_model()

class CSVDataImporter:
    @staticmethod
    def import_students(file_obj, created_by=None):
        """
        Imports students from CSV.
        Expected CSV headers:
        student_id, first_name, last_name, email, phone, gender, class, division, roll_number, dob
        """
        decoded = file_obj.read().decode('utf-8')
        io_string = io.StringIO(decoded)
        reader = csv.DictReader(io_string)

        imported_count = 0
        errors = []
        active_year = AcademicYear.objects.filter(is_active=True).first()

        for idx, row in enumerate(reader, start=2):
            try:
                stu_id = row.get('student_id', '').strip()
                f_name = row.get('first_name', '').strip()
                l_name = row.get('last_name', '').strip()
                email = row.get('email', '').strip()
                phone = row.get('phone', '').strip()
                gender = row.get('gender', 'MALE').strip().upper()
                class_name = row.get('class', '').strip()
                div_name = row.get('division', '').strip()
                roll_num = row.get('roll_number', '').strip()

                if not stu_id or not f_name or not l_name or not class_name or not div_name or not roll_num:
                    errors.append({'row': idx, 'error': "Missing required fields (student_id, first_name, last_name, class, division, roll_number)"})
                    continue

                class_obj, _ = Class.objects.get_or_create(name=class_name, defaults={'code': class_name.replace(" ", "").upper()})
                div_obj, _ = Division.objects.get_or_create(name=div_name)

                username = stu_id.lower()
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': f_name,
                        'last_name': l_name,
                        'email': email,
                        'role': User.Role.STUDENT
                    }
                )
                if user_created:
                    user.set_password('student123')
                    user.save()

                student, created = Student.objects.update_or_create(
                    student_id=stu_id,
                    defaults={
                        'user': user,
                        'first_name': f_name,
                        'last_name': l_name,
                        'email': email,
                        'phone': phone,
                        'gender': gender if gender in ['MALE', 'FEMALE', 'OTHER'] else 'MALE',
                        'class_obj': class_obj,
                        'division_obj': div_obj,
                        'roll_number': int(roll_num),
                        'academic_year': active_year
                    }
                )
                imported_count += 1
            except Exception as e:
                errors.append({'row': idx, 'error': str(e)})

        return imported_count, errors

    @staticmethod
    def import_teachers(file_obj, created_by=None):
        """
        Imports teachers from CSV.
        Expected CSV headers:
        employee_id, first_name, last_name, email, phone, department, designation
        """
        decoded = file_obj.read().decode('utf-8')
        io_string = io.StringIO(decoded)
        reader = csv.DictReader(io_string)

        imported_count = 0
        errors = []

        for idx, row in enumerate(reader, start=2):
            try:
                emp_id = row.get('employee_id', '').strip()
                f_name = row.get('first_name', '').strip()
                l_name = row.get('last_name', '').strip()
                email = row.get('email', '').strip()
                phone = row.get('phone', '').strip()
                department = row.get('department', 'Academics').strip()
                designation = row.get('designation', 'Faculty').strip()

                if not emp_id or not f_name or not l_name or not email:
                    errors.append({'row': idx, 'error': "Missing required fields (employee_id, first_name, last_name, email)"})
                    continue

                username = emp_id.lower()
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': f_name,
                        'last_name': l_name,
                        'email': email,
                        'role': User.Role.TEACHER,
                        'is_active': True
                    }
                )
                if user_created:
                    user.set_password('teacher123')
                    user.save()

                teacher, created = Teacher.objects.update_or_create(
                    employee_id=emp_id,
                    defaults={
                        'user': user,
                        'first_name': f_name,
                        'last_name': l_name,
                        'email': email,
                        'phone': phone,
                        'department': department,
                        'designation': designation
                    }
                )
                imported_count += 1
            except Exception as e:
                errors.append({'row': idx, 'error': str(e)})

        return imported_count, errors

    @staticmethod
    def import_marks(file_obj, entered_by=None):
        """
        Imports marks from CSV.
        Expected headers: student_id, exam_id, marks_obtained, remarks
        """
        decoded = file_obj.read().decode('utf-8')
        io_string = io.StringIO(decoded)
        reader = csv.DictReader(io_string)

        imported_count = 0
        errors = []

        for idx, row in enumerate(reader, start=2):
            try:
                stu_id = row.get('student_id', '').strip()
                exam_id = row.get('exam_id', '').strip()
                marks_str = row.get('marks_obtained', '').strip()
                remarks = row.get('remarks', '').strip()

                student = Student.objects.filter(student_id=stu_id).first()
                if not student:
                    errors.append({'row': idx, 'error': f"Student with ID '{stu_id}' not found."})
                    continue

                exam = Exam.objects.filter(pk=exam_id).first()
                if not exam:
                    errors.append({'row': idx, 'error': f"Exam with ID '{exam_id}' not found."})
                    continue

                marks_obtained = float(marks_str)
                if marks_obtained > float(exam.max_marks):
                    errors.append({'row': idx, 'error': f"Marks obtained ({marks_obtained}) exceeds maximum marks ({exam.max_marks})."})
                    continue

                Mark.objects.update_or_create(
                    student=student,
                    exam=exam,
                    defaults={
                        'marks_obtained': marks_obtained,
                        'remarks': remarks,
                        'entered_by': entered_by
                    }
                )
                imported_count += 1
            except Exception as e:
                errors.append({'row': idx, 'error': str(e)})

        return imported_count, errors
