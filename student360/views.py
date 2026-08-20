import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count, Sum, Q, Case, When, Value, IntegerField

from accounts.models import User
from accounts.decorators import role_required, admin_required, teacher_required, student_required, parent_required
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
from performance.services import calculate_student_hpi, get_active_setting
from awards.models import StudentAward
from awards.services import generate_student_of_the_month_suggestions
from academics.csv_importer import CSVDataImporter
from reports.services import generate_student_pdf_report, export_performance_excel_file
from meetings.models import ParentTeacherMeeting
from notifications.models import Notification
from notifications.services import send_smart_notification, send_user_notification

# Gamification Module
from gamification.models import Badge, StudentBadge, StudentGamificationProfile
from gamification.services import evaluate_and_award_student_badges, init_default_badges

# Master Intelligence Modules
from performance.ml_engine import predict_student_performance
from performance.clustering import get_student_clusters
from remarks.nlp_engine import analyze_teacher_remarks_nlp
from performance.simulator import simulate_what_if_hpi
from reports.certificates import generate_award_certificate_pdf
from audit.models import AuditLog

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        
        inactive_user = User.objects.filter(username=u, is_active=False).first()
        if inactive_user and inactive_user.check_password(p):
            messages.warning(request, "Your account registration is currently PENDING ADMIN APPROVAL. Please contact school administration.")
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=u, password=p)
        if user is not None:
            if not user.is_active:
                messages.warning(request, "Your account is inactive or pending approval.")
                return render(request, 'accounts/login.html')
            login(request, user)
            messages.success(request, f"Welcome back to EduTrack, {user.get_full_name() or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out of EduTrack.")
    return redirect('login')

def register_student_public_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    classes = Class.objects.all()
    divisions = Division.objects.all()
    active_year = AcademicYear.objects.filter(is_active=True).first()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', 'MALE')
        class_id = request.POST.get('class_id')
        division_id = request.POST.get('division_id')
        roll_number = request.POST.get('roll_number', '').strip()

        if not username or not password or not student_id or not first_name or not last_name or not class_id or not division_id or not roll_number:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/register_student.html', {'classes': classes, 'divisions': divisions})

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register_student.html', {'classes': classes, 'divisions': divisions})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'accounts/register_student.html', {'classes': classes, 'divisions': divisions})

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, f"Student ID '{student_id}' is already registered.")
            return render(request, 'accounts/register_student.html', {'classes': classes, 'divisions': divisions})

        class_obj = get_object_or_404(Class, pk=class_id)
        div_obj = get_object_or_404(Division, pk=division_id)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.STUDENT,
            phone_number=phone,
            is_active=False
        )

        student = Student.objects.create(
            user=user,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            gender=gender,
            class_obj=class_obj,
            division_obj=div_obj,
            roll_number=int(roll_number),
            academic_year=active_year
        )

        calculate_student_hpi(student)
        evaluate_and_award_student_badges(student)
        AuditLog.objects.create(user=user, action="STUDENT_SELF_REGISTER", target_student=student.full_name)

        messages.success(request, f"Student registration submitted successfully! Your EduTrack account ({username}) is currently PENDING ADMIN APPROVAL. You can log in once an Administrator approves your request.")
        return redirect('login')

    return render(request, 'accounts/register_student.html', {'classes': classes, 'divisions': divisions})

def register_teacher_public_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', 'Academics').strip()
        designation = request.POST.get('designation', 'Faculty').strip()

        if not username or not password or not employee_id or not first_name or not last_name or not email:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/register_teacher.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register_teacher.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'accounts/register_teacher.html')

        if Teacher.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f"Teacher Employee ID '{employee_id}' is already registered.")
            return render(request, 'accounts/register_teacher.html')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.TEACHER,
            phone_number=phone,
            is_active=False
        )

        teacher = Teacher.objects.create(
            user=user,
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department=department,
            designation=designation
        )

        AuditLog.objects.create(user=user, action="TEACHER_SELF_REGISTER", target_student=teacher.full_name)

        messages.success(request, f"Teacher registration submitted successfully! Your EduTrack account ({username}) is PENDING ADMIN APPROVAL.")
        return redirect('login')

    return render(request, 'accounts/register_teacher.html')

@login_required
@admin_required
def approve_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    AuditLog.objects.create(user=request.user, action="ADMIN_APPROVE_USER", target_student=user.username, new_value="Active")
    messages.success(request, f"User account '{user.username}' ({user.get_role_display()}) has been APPROVED!")
    return redirect('admin_dashboard')

@login_required
@admin_required
def reject_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    username = user.username
    user.delete()
    AuditLog.objects.create(user=request.user, action="ADMIN_REJECT_USER", target_student=username)
    messages.info(request, f"Pending registration for '{username}' was declined.")
    return redirect('admin_dashboard')

@login_required
def dashboard_view(request):
    if request.user.is_admin:
        return redirect('admin_dashboard')
    elif request.user.is_teacher:
        return redirect('teacher_dashboard')
    elif request.user.is_student:
        return redirect('student_dashboard')
    elif request.user.is_parent:
        return redirect('parent_dashboard')
    return redirect('admin_dashboard')

@login_required
@admin_required
def admin_dashboard_view(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = Class.objects.count()

    active_year = AcademicYear.objects.filter(is_active=True).first()

    if PerformanceScore.objects.count() == 0 and total_students > 0:
        for s in Student.objects.all()[:20]:
            calculate_student_hpi(s)
            evaluate_and_award_student_badges(s)

    scores = PerformanceScore.objects.all()
    avg_hpi = scores.aggregate(avg=Avg('holistic_score'))['avg'] or 75.0
    avg_att = scores.aggregate(avg=Avg('attendance_score'))['avg'] or 88.0

    at_risk_students = PerformanceScore.objects.filter(risk_level='HIGH').select_related('student', 'student__class_obj', 'student__division_obj')[:5]

    generate_student_of_the_month_suggestions()
    StudentAward.objects.filter(status=StudentAward.Status.SUGGESTED).update(status=StudentAward.Status.APPROVED)
    
    monthly_winners = StudentAward.objects.filter(
        award_type=StudentAward.AwardType.STUDENT_OF_THE_MONTH,
        status=StudentAward.Status.APPROVED
    ).select_related('student', 'student__class_obj', 'student__division_obj')[:5]

    pending_users = User.objects.filter(is_active=False).order_by('-date_joined')
    student_clusters = get_student_clusters()
    ptm_meetings = ParentTeacherMeeting.objects.select_related('student', 'teacher', 'parent')[:5]

    classes = Class.objects.all()
    divisions = Division.objects.all()
    subjects = Subject.objects.all()

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'avg_hpi': round(avg_hpi, 1),
        'avg_att': round(avg_att, 1),
        'at_risk_students': at_risk_students,
        'monthly_winners': monthly_winners,
        'pending_users': pending_users,
        'student_clusters': student_clusters,
        'ptm_meetings': ptm_meetings,
        'active_year': active_year,
        'classes': classes,
        'divisions': divisions,
        'subjects': subjects,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
@teacher_required
def teacher_dashboard_view(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher and not request.user.is_superuser:
        assigned_classes = Class.objects.all()
        my_students = Student.objects.all()
        my_ptms = ParentTeacherMeeting.objects.all()[:5]
        classes = Class.objects.all()
        divisions = Division.objects.all()
        subjects = Subject.objects.all()
    else:
        tsa_qs = TeacherSubjectAssignment.objects.filter(teacher=teacher) if teacher else []
        if tsa_qs:
            assigned_classes = Class.objects.filter(id__in=tsa_qs.values_list('class_obj_id', flat=True)).distinct()
            divisions = Division.objects.filter(id__in=tsa_qs.values_list('division_obj_id', flat=True)).distinct()
            subjects = Subject.objects.filter(id__in=tsa_qs.values_list('subject_id', flat=True)).distinct()
            classes = assigned_classes
        else:
            assigned_classes = Class.objects.all()
            classes = Class.objects.all()
            divisions = Division.objects.all()
            subjects = Subject.objects.all()

        my_students = Student.objects.filter(class_obj__in=assigned_classes)
        my_ptms = ParentTeacherMeeting.objects.filter(teacher=teacher).select_related('student', 'parent')[:5] if teacher else []

    total_assigned_students = my_students.count()
    at_risk_my_students = PerformanceScore.objects.filter(student__in=my_students, risk_level='HIGH').select_related('student')[:5]
    top_students = PerformanceScore.objects.filter(student__in=my_students).order_by('-holistic_score')[:5]

    context = {
        'teacher': teacher,
        'assigned_classes': assigned_classes,
        'total_students': total_assigned_students,
        'at_risk_students': at_risk_my_students,
        'top_students': top_students,
        'my_ptms': my_ptms,
        'classes': classes,
        'divisions': divisions,
        'subjects': subjects,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)

@login_required
def create_assignment_view(request):
    """
    Allows Teachers and Administrators to create new class assignments.
    """
    is_teacher_or_admin = request.user.is_teacher or request.user.is_admin or request.user.is_superuser or request.user.is_staff
    if not is_teacher_or_admin:
        messages.error(request, "Access restricted. Only Teachers and Administrators can create assignments.")
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        subject_id = request.POST.get('subject_id')
        class_id = request.POST.get('class_id')
        division_id = request.POST.get('division_id')
        due_date = request.POST.get('due_date')
        max_marks = request.POST.get('max_marks', 100.0)
        description = request.POST.get('description', '').strip()

        if title and subject_id and class_id and division_id and due_date:
            subject = get_object_or_404(Subject, pk=subject_id)
            class_obj = get_object_or_404(Class, pk=class_id)
            division_obj = get_object_or_404(Division, pk=division_id)

            assignment = Assignment.objects.create(
                title=title,
                subject=subject,
                class_obj=class_obj,
                division_obj=division_obj,
                assigned_by=request.user,
                due_date=due_date,
                max_marks=max_marks,
                description=description
            )

            # Audit Log
            AuditLog.objects.create(
                user=request.user,
                action="CREATE_ASSIGNMENT",
                target_student=f"{class_obj.name} {division_obj.name}",
                new_value=title
            )

            # Trigger smart notifications to all students in that class section
            class_students = Student.objects.filter(class_obj=class_obj, division_obj=division_obj)
            for s in class_students:
                send_smart_notification(
                    s,
                    title="📚 New Class Assignment Created",
                    message=f"New assignment '{title}' ({subject.name}) due on {due_date}.",
                    link='/student-dashboard/'
                )

            messages.success(request, f"Assignment '{title}' created successfully for {class_obj.name} - {division_obj.name}!")
            return redirect(request.META.get('HTTP_REFERER', 'teacher_dashboard'))
        else:
            messages.error(request, "Please fill in all required fields to create an assignment.")

    return redirect('dashboard')

@login_required
def assignments_review_view(request):
    """
    Teacher Assignment Submissions & Evaluation Portal:
    Allows teachers and admins to view all student homework submissions for their assignments and award marks.
    """
    is_teacher_or_admin = request.user.is_teacher or request.user.is_admin or request.user.is_superuser or request.user.is_staff
    if not is_teacher_or_admin:
        messages.error(request, "Access restricted. Only Teachers and Administrators can grade assignments.")
        return redirect('dashboard')

    teacher = getattr(request.user, 'teacher_profile', None)
    if teacher and not (request.user.is_superuser or request.user.is_admin):
        my_assignments = Assignment.objects.filter(assigned_by=request.user).select_related('subject', 'class_obj', 'division_obj')
        if not my_assignments.exists():
            class_ids = teacher.assignments.values_list('class_obj_id', flat=True)
            my_assignments = Assignment.objects.filter(class_obj__in=class_ids).select_related('subject', 'class_obj', 'division_obj')
    else:
        my_assignments = Assignment.objects.all().select_related('subject', 'class_obj', 'division_obj')

    selected_assignment_id = request.GET.get('assignment_id')
    selected_assignment = None
    submissions = []

    if selected_assignment_id:
        selected_assignment = my_assignments.filter(id=selected_assignment_id).first()

    if not selected_assignment and my_assignments.exists():
        selected_assignment = my_assignments.first()

    if selected_assignment:
        # Auto-create submission placeholders for all enrolled students in the class/division if not existing
        class_students = Student.objects.filter(
            class_obj=selected_assignment.class_obj,
            division_obj=selected_assignment.division_obj
        )
        for student in class_students:
            AssignmentSubmission.objects.get_or_create(
                assignment=selected_assignment,
                student=student
            )

        submissions = AssignmentSubmission.objects.filter(
            assignment=selected_assignment
        ).select_related('student', 'student__class_obj', 'student__division_obj').order_by('student__roll_number')

    submitted_count = sum(1 for s in submissions if s.status in [AssignmentSubmission.Status.SUBMITTED, AssignmentSubmission.Status.GRADED, AssignmentSubmission.Status.LATE])
    graded_count = sum(1 for s in submissions if s.status == AssignmentSubmission.Status.GRADED)
    pending_count = sum(1 for s in submissions if s.status in [AssignmentSubmission.Status.SUBMITTED, AssignmentSubmission.Status.LATE])
    
    graded_marks_list = [float(s.marks_obtained) for s in submissions if s.marks_obtained is not None]
    avg_score = round(sum(graded_marks_list) / len(graded_marks_list), 1) if graded_marks_list else 0.0

    context = {
        'my_assignments': my_assignments,
        'selected_assignment': selected_assignment,
        'submissions': submissions,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
        'pending_count': pending_count,
        'avg_score': avg_score,
    }
    return render(request, 'assignments/review.html', context)

@login_required
def grade_submission_view(request, submission_id):
    """
    Processes assignment evaluation: Saves teacher marks, quality rating, and remarks for a student submission.
    """
    is_teacher_or_admin = request.user.is_teacher or request.user.is_admin or request.user.is_superuser or request.user.is_staff
    if not is_teacher_or_admin:
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    submission = get_object_or_404(AssignmentSubmission.objects.select_related('assignment', 'student', 'student__user'), pk=submission_id)

    if request.method == 'POST':
        marks_obtained = request.POST.get('marks_obtained')
        quality_rating = request.POST.get('quality_rating', 3)
        remarks = request.POST.get('remarks', '').strip()

        if marks_obtained is not None and marks_obtained != '':
            try:
                m_val = float(marks_obtained)
                max_val = float(submission.assignment.max_marks)
                if m_val < 0 or m_val > max_val:
                    messages.error(request, f"Marks obtained must be between 0 and {max_val}.")
                    return redirect(request.META.get('HTTP_REFERER', 'assignments_review'))

                submission.marks_obtained = m_val
                submission.quality_rating = int(quality_rating)
                submission.remarks = remarks
                submission.status = AssignmentSubmission.Status.GRADED
                if not submission.submission_date:
                    submission.submission_date = datetime.date.today()
                submission.save()

                # Recalculate Student HPI Score & Badges
                calculate_student_hpi(submission.student)
                evaluate_and_award_student_badges(submission.student)

                # Audit Log
                AuditLog.objects.create(
                    user=request.user,
                    action="GRADE_ASSIGNMENT",
                    target_student=submission.student.full_name,
                    new_value=f"{submission.assignment.title}: {m_val}/{max_val} Marks"
                )

                # Smart Notification to Student
                if submission.student.user:
                    send_smart_notification(
                        submission.student.user,
                        title="📝 Assignment Graded",
                        message=f"Your assignment '{submission.assignment.title}' has been evaluated: {m_val}/{max_val} marks.",
                        link='/student-dashboard/'
                    )

                messages.success(request, f"Successfully graded {submission.student.full_name}: {m_val}/{max_val} marks!")
            except ValueError:
                messages.error(request, "Invalid marks entry.")
        else:
            messages.error(request, "Please specify valid marks obtained.")

    return redirect(request.META.get('HTTP_REFERER', 'assignments_review'))

@login_required
def student_assignments_view(request):
    """
    Dedicated Standalone Student Assignments Portal (/assignments/my/)
    Allows students to view all assigned class homework, due dates, submission status,
    marks, teacher review ratings, and submit their work on a dedicated page.
    """
    student = getattr(request.user, 'student_profile', None)
    if not student and (request.user.is_superuser or request.user.is_admin or request.user.is_teacher):
        student = Student.objects.first()
    elif not student and hasattr(request.user, 'parent_profile') and request.user.parent_profile.students.exists():
        student = request.user.parent_profile.students.first()

    if not student:
        messages.error(request, "No student profile is associated with your account.")
        return redirect('dashboard')

    class_assignments = list(Assignment.objects.filter(
        class_obj=student.class_obj,
        division_obj=student.division_obj
    ).select_related('subject', 'assigned_by').order_by('-due_date'))

    submissions = AssignmentSubmission.objects.filter(student=student).select_related('assignment')
    sub_dict = {sub.assignment_id: sub for sub in submissions}

    pending_count = 0
    submitted_count = 0
    graded_count = 0

    for a in class_assignments:
        sub = sub_dict.get(a.id)
        if sub:
            if sub.status == AssignmentSubmission.Status.GRADED:
                graded_count += 1
            else:
                submitted_count += 1
        else:
            pending_count += 1
        a.user_sub = sub

    context = {
        'student': student,
        'assignments': class_assignments,
        'total_assignments': len(class_assignments),
        'pending_count': pending_count,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
    }
    return render(request, 'assignments/student_assignments.html', context)

@login_required
@student_required
def student_dashboard_view(request):
    student = getattr(request.user, 'student_profile', None)
    if not student and request.user.is_superuser:
        student = Student.objects.first()

    if not student:
        messages.error(request, "No student profile is associated with your account.")
        return redirect('login')

    perf = PerformanceScore.objects.filter(student=student).first()
    if not perf:
        perf = calculate_student_hpi(student)

    g_profile = evaluate_and_award_student_badges(student)
    earned_badges = StudentBadge.objects.filter(student=student).select_related('badge')[:5]

    marks = Mark.objects.filter(student=student).select_related('exam', 'exam__subject').order_by('-exam__date')[:10]
    remarks = TeacherRemark.objects.filter(student=student).select_related('teacher').order_by('-date')[:5]
    awards = StudentAward.objects.filter(student=student, status=StudentAward.Status.APPROVED)
    
    class_assignments = list(Assignment.objects.filter(
        class_obj=student.class_obj,
        division_obj=student.division_obj
    ).select_related('subject', 'assigned_by'))
    submissions = AssignmentSubmission.objects.filter(student=student).select_related('assignment')
    sub_dict = {sub.assignment_id: sub for sub in submissions}
    for a in class_assignments:
        a.user_sub = sub_dict.get(a.id)

    ml_pred = predict_student_performance(student)
    nlp_remarks = analyze_teacher_remarks_nlp(student)

    context = {
        'student': student,
        'perf': perf,
        'g_profile': g_profile,
        'earned_badges': earned_badges,
        'marks': marks,
        'remarks': remarks,
        'awards': awards,
        'class_assignments': class_assignments,
        'ml_pred': ml_pred,
        'nlp_remarks': nlp_remarks,
    }
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
def gamification_hub_view(request):
    init_default_badges()

    for s in Student.objects.all():
        evaluate_and_award_student_badges(s)

    current_student = getattr(request.user, 'student_profile', None)
    if not current_student and request.user.is_superuser:
        current_student = Student.objects.first()

    my_profile = evaluate_and_award_student_badges(current_student) if current_student else None
    my_earned_badge_ids = set(StudentBadge.objects.filter(student=current_student).values_list('badge_id', flat=True)) if current_student else set()

    all_badges = Badge.objects.all()
    leaderboard = StudentGamificationProfile.objects.select_related('student', 'student__class_obj', 'student__division_obj').order_by('-total_xp')[:15]
    my_awards = StudentAward.objects.filter(student=current_student, status=StudentAward.Status.APPROVED) if current_student else []

    context = {
        'current_student': current_student,
        'my_profile': my_profile,
        'my_earned_badge_ids': my_earned_badge_ids,
        'all_badges': all_badges,
        'leaderboard': leaderboard,
        'my_awards': my_awards,
    }
    return render(request, 'gamification/hub.html', context)

@login_required
@student_required
def submit_assignment_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "No student profile found.")
        return redirect('student_dashboard')

    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip() or "Homework submitted online by student."
        
        AssignmentSubmission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                'submission_date': datetime.date.today(),
                'status': AssignmentSubmission.Status.SUBMITTED,
                'remarks': remarks
            }
        )
        calculate_student_hpi(student)
        evaluate_and_award_student_badges(student)
        AuditLog.objects.create(user=request.user, action="SUBMIT_ASSIGNMENT", target_student=student.full_name, new_value=assignment.title)
        messages.success(request, f"Assignment '{assignment.title}' submitted successfully!")

    return redirect('student_dashboard')

@login_required
@parent_required
def parent_dashboard_view(request):
    """
    Strictly isolated Parent Dashboard:
    Parents can ONLY view details and reports for their linked child/children.
    """
    parent = getattr(request.user, 'parent_profile', None)
    if parent:
        students = parent.students.all()
        my_ptms = ParentTeacherMeeting.objects.filter(parent=parent).select_related('student', 'teacher')[:5]
    else:
        students = Student.objects.all()[:1]
        my_ptms = ParentTeacherMeeting.objects.all()[:5]

    first_child = students.first() if students.exists() else None
    perf = PerformanceScore.objects.filter(student=first_child).first() if first_child else None

    marks = Mark.objects.filter(student=first_child).select_related('exam', 'exam__subject').order_by('-exam__date')[:5] if first_child else []
    awards = StudentAward.objects.filter(student=first_child, status=StudentAward.Status.APPROVED) if first_child else []

    context = {
        'parent': parent,
        'students': students,
        'child': first_child,
        'perf': perf,
        'marks': marks,
        'awards': awards,
        'my_ptms': my_ptms,
    }
    return render(request, 'dashboard/parent_dashboard.html', context)

# --- NOTIFICATIONS PORTAL VIEWS ---

@login_required
def notifications_list_view(request):
    """
    Notifications Portal Hub: Lists all smart notifications for the logged-in user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_notification_read_view(request, pk):
    """
    Marks a notification as read.
    """
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications_list')

# --- PARENT TEACHER MEETING (PTM) PORTAL VIEWS ---

@login_required
def ptm_list_view(request):
    user = request.user
    meetings = ParentTeacherMeeting.objects.select_related('teacher', 'student', 'parent').all()
    current_teacher = getattr(user, 'teacher_profile', None)

    if user.is_teacher and not user.is_superuser:
        if current_teacher:
            meetings = meetings.filter(teacher=current_teacher)
    elif user.is_parent and not user.is_superuser:
        parent = getattr(user, 'parent_profile', None)
        if parent:
            meetings = meetings.filter(parent=parent)
    elif user.is_student and not user.is_superuser:
        student = getattr(user, 'student_profile', None)
        if student:
            meetings = meetings.filter(student=student)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        meetings = meetings.filter(status=status_filter)

    teachers = Teacher.objects.all()
    students = Student.objects.all()
    parents = Parent.objects.all()

    context = {
        'meetings': meetings,
        'teachers': teachers,
        'students': students,
        'parents': parents,
        'current_teacher': current_teacher,
        'selected_status': status_filter,
    }
    return render(request, 'meetings/ptm_list.html', context)

@login_required
def ptm_schedule_view(request):
    is_teacher_or_admin = request.user.is_teacher or request.user.is_admin or request.user.is_superuser or request.user.is_staff
    if not is_teacher_or_admin:
        messages.error(request, "Only Teachers and Administrators are permitted to schedule Parent-Teacher Meetings.")
        return redirect('ptm_list')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip() or "Parent-Teacher Performance Meeting"
        teacher_id = request.POST.get('teacher_id')
        
        # If logged in as Teacher, lock teacher_id to current teacher's profile
        if request.user.is_teacher and not request.user.is_superuser:
            current_teacher = getattr(request.user, 'teacher_profile', None)
            if current_teacher:
                teacher_id = current_teacher.id

        student_id = request.POST.get('student_id')
        meeting_date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        meeting_type = request.POST.get('meeting_type', 'ONLINE')
        location_or_link = request.POST.get('location_or_link', '').strip() or "https://meet.google.com/edutrack-ptm"
        agenda_notes = request.POST.get('agenda_notes', '').strip()

        teacher_obj = get_object_or_404(Teacher, pk=teacher_id)
        student_obj = get_object_or_404(Student, pk=student_id)
        parent_obj = Parent.objects.filter(students=student_obj).first()

        status_val = ParentTeacherMeeting.Status.SCHEDULED
        if request.user.is_parent:
            status_val = ParentTeacherMeeting.Status.REQUESTED

        ptm = ParentTeacherMeeting.objects.create(
            title=title,
            teacher=teacher_obj,
            student=student_obj,
            parent=parent_obj,
            date=meeting_date,
            start_time=start_time,
            end_time=end_time,
            meeting_type=meeting_type,
            location_or_link=location_or_link,
            status=status_val,
            agenda_notes=agenda_notes,
            requested_by=request.user
        )

        AuditLog.objects.create(
            user=request.user,
            action="SCHEDULE_PTM",
            target_student=student_obj.full_name,
            new_value=f"PTM on {meeting_date} at {start_time}"
        )

        # Trigger Smart Notification to Student & Parent
        send_smart_notification(
            student_obj,
            title="🤝 Parent-Teacher Meeting Scheduled",
            message=f"A PTM '{title}' has been scheduled for {student_obj.full_name} with {teacher_obj.full_name} on {meeting_date} at {start_time}.",
            link='/meetings/'
        )

        messages.success(request, f"Parent-Teacher Meeting scheduled successfully for {student_obj.full_name} on {meeting_date}!")
        return redirect('ptm_list')

    return redirect('ptm_list')

@login_required
def ptm_update_status_view(request, pk):
    ptm = get_object_or_404(ParentTeacherMeeting, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        feedback = request.POST.get('summary_feedback', '').strip()

        if new_status:
            ptm.status = new_status
        if feedback and not request.user.is_student:
            ptm.summary_feedback = feedback

        ptm.save()
        AuditLog.objects.create(
            user=request.user,
            action="UPDATE_PTM_STATUS",
            target_student=ptm.student.full_name,
            new_value=f"Status: {ptm.status}"
        )
        messages.success(request, f"PTM record updated for {ptm.student.full_name}!")

    return redirect('ptm_list')

@login_required
@teacher_required
def add_student_view(request):
    classes = Class.objects.all()
    divisions = Division.objects.all()
    active_year = AcademicYear.objects.filter(is_active=True).first()

    if request.method == 'POST':
        student_id = request.POST.get('student_id', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        gender = request.POST.get('gender', 'MALE')
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        class_id = request.POST.get('class_id')
        division_id = request.POST.get('division_id')
        roll_number = request.POST.get('roll_number', '').strip()
        password = request.POST.get('password', '').strip() or 'student123'

        if not student_id or not first_name or not last_name or not class_id or not division_id or not roll_number:
            messages.error(request, "Please fill in all required fields.")
            return redirect(request.META.get('HTTP_REFERER', 'student_list'))

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, f"Student ID '{student_id}' already exists!")
            return redirect(request.META.get('HTTP_REFERER', 'student_list'))

        class_obj = get_object_or_404(Class, pk=class_id)
        div_obj = get_object_or_404(Division, pk=division_id)

        username = student_id.lower()
        user, u_created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'role': User.Role.STUDENT,
                'is_active': True
            }
        )
        if u_created:
            user.set_password(password)
            user.save()

        student = Student.objects.create(
            user=user,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            email=email,
            phone=phone,
            class_obj=class_obj,
            division_obj=div_obj,
            roll_number=int(roll_number),
            academic_year=active_year
        )

        calculate_student_hpi(student)
        evaluate_and_award_student_badges(student)
        AuditLog.objects.create(user=request.user, action="ADD_STUDENT", target_student=student.full_name)

        messages.success(request, f"Student {student.full_name} ({student.student_id}) added successfully!")
        return redirect('student_detail', pk=student.id)

    context = {'classes': classes, 'divisions': divisions}
    return render(request, 'students/add_student.html', context)

@login_required
def student_list_view(request):
    if request.user.is_student and not request.user.is_superuser:
        student = getattr(request.user, 'student_profile', None)
        if student:
            return redirect('student_detail', pk=student.id)
        else:
            return redirect('student_dashboard')

    # Remove Student Roster Access from Parents
    if request.user.is_parent and not request.user.is_superuser:
        messages.error(request, "Access restricted. Parents do not have access to the full student roster.")
        return redirect('parent_dashboard')

    query = request.GET.get('q', '').strip()
    class_id = request.GET.get('class', '')

    students = Student.objects.select_related('class_obj', 'division_obj')

    if request.user.is_teacher and not request.user.is_superuser:
        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher:
            assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
            class_ids = [a.class_obj.id for a in assignments]
            students = students.filter(class_obj__in=class_ids)

    if query:
        students = students.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(student_id__icontains=query)
        )
    if class_id:
        students = students.filter(class_obj_id=class_id)

    classes = Class.objects.all()
    divisions = Division.objects.all()
    context = {'students': students, 'classes': classes, 'divisions': divisions, 'query': query, 'selected_class': class_id}
    return render(request, 'students/student_list.html', context)

@login_required
def teacher_list_view(request):
    if (request.user.is_student or request.user.is_parent) and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    dept = request.GET.get('dept', '').strip()

    teachers = Teacher.objects.prefetch_related('assignments', 'assignments__class_obj', 'assignments__subject').all()

    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(employee_id__icontains=query)
        )
    if dept:
        teachers = teachers.filter(department__icontains=dept)

    departments = Teacher.objects.values_list('department', flat=True).distinct()

    context = {
        'teachers': teachers,
        'query': query,
        'selected_dept': dept,
        'departments': departments,
    }
    return render(request, 'teachers/teacher_list.html', context)

@login_required
@teacher_required
def indicators_entry_view(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    if request.user.is_teacher and not request.user.is_superuser and teacher:
        t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
        assigned_classes = [a.class_obj.id for a in t_assignments]
        assigned_subjects = [a.subject.id for a in t_assignments]
        students = Student.objects.filter(class_obj__in=assigned_classes).select_related('class_obj', 'division_obj')
        assignments = Assignment.objects.filter(class_obj__in=assigned_classes, subject__in=assigned_subjects).select_related('subject', 'class_obj', 'division_obj')
    else:
        students = Student.objects.select_related('class_obj', 'division_obj').all()
        assignments = Assignment.objects.select_related('subject', 'class_obj', 'division_obj').all()

    if request.method == 'POST':
        indicator_type = request.POST.get('indicator_type')
        student_id = request.POST.get('student_id')
        student = get_object_or_404(Student, pk=student_id)
        today = datetime.date.today()

        if indicator_type == 'behaviour':
            discipline = int(request.POST.get('discipline', 3))
            respect = int(request.POST.get('respect', 3))
            responsibility = int(request.POST.get('responsibility', 3))
            cooperation = int(request.POST.get('cooperation', 3))
            punctuality = int(request.POST.get('punctuality', 3))
            conduct = int(request.POST.get('classroom_conduct', 3))
            leadership = int(request.POST.get('leadership', 3))
            teamwork = int(request.POST.get('teamwork', 3))
            notes = request.POST.get('notes', '')

            BehaviourRecord.objects.create(
                student=student,
                date=today,
                discipline=discipline,
                respect=respect,
                responsibility=responsibility,
                cooperation=cooperation,
                punctuality=punctuality,
                classroom_conduct=conduct,
                leadership=leadership,
                teamwork=teamwork,
                recorded_by=request.user,
                notes=notes
            )
            AuditLog.objects.create(user=request.user, action="LOG_BEHAVIOUR", target_student=student.full_name)
            messages.success(request, f"Logged Behaviour Rating for {student.full_name}!")

        elif indicator_type == 'participation':
            class_p = int(request.POST.get('class_participation', 3))
            q_asking = int(request.POST.get('question_asking', 3))
            pres = int(request.POST.get('presentation', 3))
            group = int(request.POST.get('group_activities', 3))
            lead = int(request.POST.get('leadership', 3))
            extra = int(request.POST.get('extracurricular', 3))
            notes = request.POST.get('notes', '')

            Participation.objects.create(
                student=student,
                date=today,
                class_participation=class_p,
                question_asking=q_asking,
                presentation=pres,
                group_activities=group,
                leadership=lead,
                extracurricular=extra,
                recorded_by=request.user,
                notes=notes
            )
            AuditLog.objects.create(user=request.user, action="LOG_PARTICIPATION", target_student=student.full_name)
            messages.success(request, f"Logged Class Participation Score for {student.full_name}!")

        elif indicator_type == 'assignment':
            assignment_id = request.POST.get('assignment_id')
            marks_obtained = request.POST.get('marks_obtained', 0)
            quality_rating = int(request.POST.get('quality_rating', 3))
            remarks = request.POST.get('remarks', '')

            assignment_obj = get_object_or_404(Assignment, pk=assignment_id)
            AssignmentSubmission.objects.update_or_create(
                assignment=assignment_obj,
                student=student,
                defaults={
                    'submission_date': today,
                    'status': AssignmentSubmission.Status.GRADED,
                    'marks_obtained': float(marks_obtained),
                    'quality_rating': quality_rating,
                    'remarks': remarks
                }
            )
            AuditLog.objects.create(user=request.user, action="LOG_ASSIGNMENT", target_student=student.full_name)
            messages.success(request, f"Logged Assignment Score for {student.full_name}!")

        elif indicator_type == 'improvement':
            imp_score = float(request.POST.get('improvement_score', 75))
            active_year = AcademicYear.objects.filter(is_active=True).first()
            now = datetime.datetime.now()

            perf, _ = PerformanceScore.objects.get_or_create(
                student=student,
                academic_year=active_year,
                month=now.month,
                year=now.year
            )
            perf.improvement_score = imp_score
            perf.save()
            AuditLog.objects.create(user=request.user, action="UPDATE_IMPROVEMENT", target_student=student.full_name, new_value=str(imp_score))
            messages.success(request, f"Updated Improvement Index ({imp_score}%) for {student.full_name}!")

        elif indicator_type == 'achievement':
            title = request.POST.get('title', '').strip()
            category = request.POST.get('category', 'ACADEMIC')
            level = request.POST.get('level', 'SCHOOL')
            points = int(request.POST.get('points', 10))
            description = request.POST.get('description', '')

            Achievement.objects.create(
                student=student,
                title=title,
                category=category,
                level=level,
                points=points,
                date=today,
                awarded_by=request.user,
                description=description
            )
            AuditLog.objects.create(user=request.user, action="LOG_ACHIEVEMENT", target_student=student.full_name, new_value=title)
            messages.success(request, f"Logged Achievement '{title}' for {student.full_name}!")

        calculate_student_hpi(student)
        evaluate_and_award_student_badges(student)
        return redirect(request.META.get('HTTP_REFERER', 'indicators_entry'))

    context = {
        'students': students,
        'assignments': assignments,
    }
    return render(request, 'performance/indicators_entry.html', context)

@login_required
def student_detail_view(request, pk):
    student = get_object_or_404(Student.objects.select_related('class_obj', 'division_obj', 'academic_year'), pk=pk)

    if request.user.is_student and not request.user.is_superuser:
        my_student = getattr(request.user, 'student_profile', None)
        if not my_student or my_student.pk != student.pk:
            messages.error(request, "Access restricted. You can only view your own student performance profile.")
            if my_student:
                return redirect('student_detail', pk=my_student.pk)
            return redirect('student_dashboard')

    if request.user.is_parent and not request.user.is_superuser:
        parent = getattr(request.user, 'parent_profile', None)
        if parent:
            child_ids = [c.id for c in parent.students.all()]
            if student.pk not in child_ids:
                messages.error(request, "Access restricted. You can only view performance details of your own child.")
                return redirect('parent_dashboard')

    perf = PerformanceScore.objects.filter(student=student).first()
    if not perf:
        perf = calculate_student_hpi(student)

    g_profile = evaluate_and_award_student_badges(student)
    earned_badges = StudentBadge.objects.filter(student=student).select_related('badge')

    marks = Mark.objects.filter(student=student).select_related('exam', 'exam__subject').order_by('-exam__date')
    attendance = Attendance.objects.filter(student=student).order_by('-date')[:30]
    behaviour = BehaviourRecord.objects.filter(student=student).order_by('-date')[:10]
    assignments = AssignmentSubmission.objects.filter(student=student).select_related('assignment')
    achievements = Achievement.objects.filter(student=student)
    remarks = TeacherRemark.objects.filter(student=student).select_related('teacher')
    awards = StudentAward.objects.filter(student=student)
    ptms = ParentTeacherMeeting.objects.filter(student=student).select_related('teacher', 'parent')[:5]

    ml_pred = predict_student_performance(student)
    nlp_remarks = analyze_teacher_remarks_nlp(student)
    curr_hpi, proj_hpi, delta_hpi = simulate_what_if_hpi(perf, att_delta=15, acad_delta=10, ass_delta=20)
    audit_logs = AuditLog.objects.filter(target_student=student.full_name)[:5]

    context = {
        'student': student,
        'perf': perf,
        'g_profile': g_profile,
        'earned_badges': earned_badges,
        'marks': marks,
        'attendance': attendance,
        'behaviour': behaviour,
        'assignments': assignments,
        'achievements': achievements,
        'remarks': remarks,
        'awards': awards,
        'ptms': ptms,
        'ml_pred': ml_pred,
        'nlp_remarks': nlp_remarks,
        'sim_curr_hpi': curr_hpi,
        'sim_proj_hpi': proj_hpi,
        'sim_delta_hpi': delta_hpi,
        'audit_logs': audit_logs,
    }
    return render(request, 'students/student_detail.html', context)

@login_required
@teacher_required
def marks_entry_view(request):
    exams = Exam.objects.select_related('subject', 'class_obj', 'division_obj').all()

    if request.user.is_teacher and not request.user.is_superuser:
        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher:
            t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
            assigned_classes = [a.class_obj.id for a in t_assignments]
            assigned_subjects = [a.subject.id for a in t_assignments]
            exams = exams.filter(class_obj__in=assigned_classes, subject__in=assigned_subjects)

    selected_exam_id = request.GET.get('exam_id') or (exams.first().id if exams.exists() else None)
    selected_exam = Exam.objects.filter(pk=selected_exam_id).first() if selected_exam_id else None

    if selected_exam and request.user.is_teacher and not request.user.is_superuser:
        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher:
            t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
            assigned_classes = [a.class_obj.id for a in t_assignments]
            assigned_subjects = [a.subject.id for a in t_assignments]
            if selected_exam.class_obj.id not in assigned_classes or selected_exam.subject.id not in assigned_subjects:
                messages.error(request, "Access denied. You are only authorized to enter marks for your assigned classes and subjects.")
                return redirect('dashboard')

    students = []
    existing_marks_dict = {}

    if selected_exam:
        students = Student.objects.filter(class_obj=selected_exam.class_obj)
        if selected_exam.division_obj:
            students = students.filter(division_obj=selected_exam.division_obj)

        marks_qs = Mark.objects.filter(exam=selected_exam)
        existing_marks_dict = {m.student_id: float(m.marks_obtained) for m in marks_qs}

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        exam_obj = get_object_or_404(Exam, pk=exam_id)

        if request.user.is_teacher and not request.user.is_superuser:
            teacher = getattr(request.user, 'teacher_profile', None)
            if teacher:
                t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
                assigned_classes = [a.class_obj.id for a in t_assignments]
                assigned_subjects = [a.subject.id for a in t_assignments]
                if exam_obj.class_obj.id not in assigned_classes or exam_obj.subject.id not in assigned_subjects:
                    messages.error(request, "Access denied. You are only authorized to enter marks for your assigned classes and subjects.")
                    return redirect('dashboard')

        saved_count = 0
        for key, val in request.POST.items():
            if key.startswith('mark_'):
                student_pk = key.replace('mark_', '')
                if val.strip() != '':
                    try:
                        obtained = float(val)
                        if obtained > float(exam_obj.max_marks):
                            messages.error(request, f"Marks ({obtained}) for student cannot exceed max marks ({exam_obj.max_marks}).")
                            continue

                        student_obj = Student.objects.get(pk=student_pk)
                        Mark.objects.update_or_create(
                            student=student_obj,
                            exam=exam_obj,
                            defaults={
                                'marks_obtained': obtained,
                                'entered_by': request.user
                            }
                        )
                        calculate_student_hpi(student_obj)
                        evaluate_and_award_student_badges(student_obj)

                        send_smart_notification(
                            student_obj,
                            title="📝 Exam Marks Published",
                            message=f"New exam marks recorded for {exam_obj.subject.name} - {exam_obj.title}: {obtained}/{exam_obj.max_marks}.",
                            link='/dashboard/'
                        )

                        saved_count += 1
                    except Exception as e:
                        messages.error(request, f"Error saving marks: {str(e)}")

        AuditLog.objects.create(user=request.user, action="ENTER_MARKS", target_student=f"Exam: {exam_obj.subject.name} - {exam_obj.class_obj.name}")
        messages.success(request, f"Successfully recorded {saved_count} marks entries!")
        return redirect(f"/marks/entry/?exam_id={exam_id}")

    context = {
        'exams': exams,
        'selected_exam': selected_exam,
        'students': students,
        'existing_marks': existing_marks_dict
    }
    return render(request, 'academics/marks_entry.html', context)

@login_required
@teacher_required
def attendance_entry_view(request):
    classes = Class.objects.all()
    divisions = Division.objects.all()

    if request.user.is_teacher and not request.user.is_superuser:
        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher:
            t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
            assigned_classes = [a.class_obj.id for a in t_assignments]
            classes = classes.filter(id__in=assigned_classes)

    class_id = request.GET.get('class_id') or (classes.first().id if classes.exists() else None)
    div_id = request.GET.get('div_id') or (divisions.first().id if divisions.exists() else None)
    date_str = request.GET.get('date') or datetime.date.today().isoformat()

    selected_class = Class.objects.filter(pk=class_id).first()
    selected_div = Division.objects.filter(pk=div_id).first()

    if selected_class and request.user.is_teacher and not request.user.is_superuser:
        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher:
            t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
            assigned_classes = [a.class_obj.id for a in t_assignments]
            if selected_class.id not in assigned_classes:
                messages.error(request, "Access denied. You are only authorized to mark attendance for your assigned classes.")
                return redirect('dashboard')

    students = Student.objects.filter(class_obj=selected_class, division_obj=selected_div) if selected_class and selected_div else []

    existing_att = {}
    if students:
        att_qs = Attendance.objects.filter(class_obj=selected_class, division_obj=selected_div, date=date_str)
        existing_att = {a.student_id: a.status for a in att_qs}

    if request.method == 'POST':
        req_date = request.POST.get('date')
        req_class_id = request.POST.get('class_id')
        req_div_id = request.POST.get('div_id')

        cls_obj = get_object_or_404(Class, pk=req_class_id)
        div_obj = get_object_or_404(Division, pk=req_div_id)

        if request.user.is_teacher and not request.user.is_superuser:
            teacher = getattr(request.user, 'teacher_profile', None)
            if teacher:
                t_assignments = TeacherSubjectAssignment.objects.filter(teacher=teacher)
                assigned_classes = [a.class_obj.id for a in t_assignments]
                if cls_obj.id not in assigned_classes:
                    messages.error(request, "Access denied. You are only authorized to mark attendance for your assigned classes.")
                    return redirect('dashboard')

        stu_list = Student.objects.filter(class_obj=cls_obj, division_obj=div_obj)
        count = 0
        for s in stu_list:
            status_val = request.POST.get(f"att_{s.id}", "PRESENT")
            Attendance.objects.update_or_create(
                student=s,
                date=req_date,
                defaults={
                    'class_obj': cls_obj,
                    'division_obj': div_obj,
                    'status': status_val,
                    'marked_by': request.user
                }
            )
            calculate_student_hpi(s)
            evaluate_and_award_student_badges(s)

            if status_val == Attendance.Status.ABSENT:
                send_smart_notification(
                    s,
                    title="🚨 Absence Alert: Student Absent Today",
                    message=f"{s.full_name} was marked ABSENT on {req_date}.",
                    link='/dashboard/'
                )
            elif status_val == Attendance.Status.LATE:
                send_smart_notification(
                    s,
                    title="⚠️ Attendance Alert: Student Marked Late",
                    message=f"{s.full_name} was marked LATE on {req_date}.",
                    link='/dashboard/'
                )

            count += 1

        AuditLog.objects.create(user=request.user, action="MARK_ATTENDANCE", target_student=f"{cls_obj.name}-{div_obj.name} on {req_date}")
        messages.success(request, f"Attendance marked for {count} students on {req_date}!")
        return redirect(f"/attendance/mark/?class_id={req_class_id}&div_id={req_div_id}&date={req_date}")

    context = {
        'classes': classes,
        'divisions': divisions,
        'selected_class': selected_class,
        'selected_div': selected_div,
        'date_str': date_str,
        'students': students,
        'existing_att': existing_att
    }
    return render(request, 'attendance/attendance_entry.html', context)

@login_required
@admin_required
def awards_management_view(request):
    awards = StudentAward.objects.select_related('student', 'student__class_obj', 'student__division_obj').all()
    context = {'awards': awards}
    return render(request, 'awards/awards_list.html', context)

@login_required
def download_certificate_pdf_view(request, award_id):
    award = get_object_or_404(StudentAward, pk=award_id)

    if request.user.is_student and not request.user.is_superuser:
        my_student = getattr(request.user, 'student_profile', None)
        if not my_student or my_student.pk != award.student.pk:
            messages.error(request, "Access restricted. You can only download your own Award Certificate.")
            return redirect('dashboard')

    pdf_buffer = generate_award_certificate_pdf(award)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificate_{award.student.student_id}_{award.award_type}.pdf"'
    return response

@login_required
@admin_required
def approve_award_view(request, pk):
    award = get_object_or_404(StudentAward, pk=pk)
    award.status = StudentAward.Status.APPROVED
    award.approved_by = request.user
    award.save()
    
    send_smart_notification(
        award.student,
        title="🏆 Congratulations! Student Award Approved!",
        message=f"Congratulations! {award.student.full_name}'s award '{award.get_award_type_display()}' has been approved by School Administration.",
        link='/dashboard/'
    )

    messages.success(request, f"Award approved for {award.student.full_name}!")
    return redirect('awards_management')

@login_required
@admin_required
def at_risk_monitoring_view(request):
    scores = PerformanceScore.objects.select_related('student', 'student__class_obj', 'student__division_obj').all()

    high_risk_list = scores.filter(risk_level='HIGH')
    medium_risk_list = scores.filter(risk_level='MEDIUM')
    low_risk_list = scores.filter(risk_level='LOW')

    high_risk_count = high_risk_list.count()
    medium_risk_count = medium_risk_list.count()
    low_risk_count = low_risk_list.count()
    total_students = scores.count() or 1
    healthy_count = max(0, total_students - (high_risk_count + medium_risk_count))

    flagged_scores = scores.filter(risk_level__in=['HIGH', 'MEDIUM'])
    avg_at_risk_hpi = round(flagged_scores.aggregate(avg=Avg('holistic_score'))['avg'] or 0.0, 1)
    critical_att_count = scores.filter(attendance_score__lt=75.0).count()

    classes = Class.objects.all()
    class_risk_labels = []
    class_risk_counts = []
    for c in classes:
        cnt = scores.filter(student__class_obj=c, risk_level__in=['HIGH', 'MEDIUM']).count()
        class_risk_labels.append(c.name)
        class_risk_counts.append(cnt)

    at_risk_list = flagged_scores.annotate(
        risk_order=Case(
            When(risk_level='HIGH', then=Value(1)),
            When(risk_level='MEDIUM', then=Value(2)),
            When(risk_level='LOW', then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by('risk_order', 'holistic_score')

    context = {
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
        'healthy_count': healthy_count,
        'total_students': total_students,
        'avg_at_risk_hpi': avg_at_risk_hpi,
        'critical_att_count': critical_att_count,
        'class_risk_labels': class_risk_labels,
        'class_risk_counts': class_risk_counts,
        'at_risk_list': at_risk_list,
    }
    return render(request, 'analytics/at_risk.html', context)

@login_required
def class_analytics_view(request):
    classes = Class.objects.all()
    selected_class_id = request.GET.get('class_id') or (classes.first().id if classes.exists() else None)
    selected_class = Class.objects.filter(pk=selected_class_id).first()

    stats = {}
    if selected_class:
        students = Student.objects.filter(class_obj=selected_class)
        scores = PerformanceScore.objects.filter(student__in=students)
        stats = {
            'total_students': students.count(),
            'avg_hpi': round(scores.aggregate(avg=Avg('holistic_score'))['avg'] or 0, 1),
            'avg_acad': round(scores.aggregate(avg=Avg('academic_score'))['avg'] or 0, 1),
            'avg_att': round(scores.aggregate(avg=Avg('attendance_score'))['avg'] or 0, 1),
            'at_risk_count': scores.filter(risk_level='HIGH').count()
        }

    context = {'classes': classes, 'selected_class': selected_class, 'stats': stats}
    return render(request, 'analytics/class_analytics.html', context)

@login_required
@admin_required
def settings_view(request):
    active_year = AcademicYear.objects.filter(is_active=True).first()
    setting = get_active_setting(active_year)

    if request.method == 'POST':
        setting.weight_academic = float(request.POST.get('weight_academic', 40))
        setting.weight_attendance = float(request.POST.get('weight_attendance', 15))
        setting.weight_behaviour = float(request.POST.get('weight_behaviour', 15))
        setting.weight_participation = float(request.POST.get('weight_participation', 10))
        setting.weight_assignments = float(request.POST.get('weight_assignments', 5))
        setting.weight_improvement = float(request.POST.get('weight_improvement', 10))
        setting.weight_achievements = float(request.POST.get('weight_achievements', 5))
        setting.min_attendance_threshold = float(request.POST.get('min_attendance_threshold', 75))
        setting.save()

        for s in Student.objects.all():
            calculate_student_hpi(s)
            evaluate_and_award_student_badges(s)

        messages.success(request, "Performance weights updated successfully and scores recalculated!")
        return redirect('settings')

    context = {'setting': setting, 'active_year': active_year}
    return render(request, 'settings.html', context)

@login_required
@admin_required
def csv_import_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        import_type = request.POST.get('import_type')
        csv_file = request.FILES['csv_file']

        if import_type == 'students':
            count, errors = CSVDataImporter.import_students(csv_file, request.user)
            messages.success(request, f"Imported {count} students successfully!")
        elif import_type == 'teachers':
            count, errors = CSVDataImporter.import_teachers(csv_file, request.user)
            messages.success(request, f"Imported {count} teachers successfully!")
        elif import_type == 'marks':
            count, errors = CSVDataImporter.import_marks(csv_file, request.user)
            messages.success(request, f"Imported {count} marks entries successfully!")
        else:
            messages.error(request, "Invalid import type selected.")

    return render(request, 'reports/import.html')

@login_required
def report_center_view(request):
    if request.user.is_student and not request.user.is_superuser:
        student = getattr(request.user, 'student_profile', None)
        students = Student.objects.filter(pk=student.pk) if student else Student.objects.none()
    elif request.user.is_parent and not request.user.is_superuser:
        parent = getattr(request.user, 'parent_profile', None)
        students = parent.students.all() if parent else Student.objects.none()
    else:
        students = Student.objects.all()

    return render(request, 'reports/report_center.html', {'students': students})

@login_required
def download_pdf_report_view(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    if request.user.is_student and not request.user.is_superuser:
        my_student = getattr(request.user, 'student_profile', None)
        if not my_student or my_student.pk != student.pk:
            messages.error(request, "Access restricted. You can only download your own progress report PDF.")
            return redirect('dashboard')

    if request.user.is_parent and not request.user.is_superuser:
        parent = getattr(request.user, 'parent_profile', None)
        if parent:
            child_ids = [c.id for c in parent.students.all()]
            if student.pk not in child_ids:
                messages.error(request, "Access restricted. You can only download progress reports of your own child.")
                return redirect('parent_dashboard')

    pdf_buffer = generate_student_pdf_report(student)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="EduTrack_{student.student_id}_Report.pdf"'
    return response

@login_required
def export_excel_report_view(request):
    if (request.user.is_student or request.user.is_parent) and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    excel_buffer = export_performance_excel_file()
    response = HttpResponse(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="EduTrack_Performance_Report.xlsx"'
    return response
