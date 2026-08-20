from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from student360 import views, api_views

router = DefaultRouter()
router.register(r'students', api_views.StudentViewSet)
router.register(r'teachers', api_views.TeacherViewSet)
router.register(r'classes', api_views.ClassViewSet)
router.register(r'subjects', api_views.SubjectViewSet)
router.register(r'exams', api_views.ExamViewSet)
router.register(r'marks', api_views.MarkViewSet)
router.register(r'attendance', api_views.AttendanceViewSet)
router.register(r'behaviour', api_views.BehaviourViewSet)
router.register(r'assignments', api_views.AssignmentViewSet)
router.register(r'participation', api_views.ParticipationViewSet)
router.register(r'achievements', api_views.AchievementViewSet)
router.register(r'remarks', api_views.TeacherRemarkViewSet)
router.register(r'performance', api_views.PerformanceScoreViewSet)
router.register(r'awards', api_views.StudentAwardViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth & Self-Registration
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/student/', views.register_student_public_view, name='register_student'),
    path('register/teacher/', views.register_teacher_public_view, name='register_teacher'),
    
    # User Approval Workflow
    path('users/<int:pk>/approve/', views.approve_user_view, name='approve_user'),
    path('users/<int:pk>/reject/', views.reject_user_view, name='reject_user'),
    
    # Role Dashboards
    path('', views.dashboard_view, name='root'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('parent-dashboard/', views.parent_dashboard_view, name='parent_dashboard'),
    
    # Student Modules, Standalone Assignments Portal & Submissions
    path('students/', views.student_list_view, name='student_list'),
    path('students/add/', views.add_student_view, name='add_student'),
    path('students/<int:pk>/', views.student_detail_view, name='student_detail'),
    path('assignments/create/', views.create_assignment_view, name='create_assignment'),
    path('assignments/my/', views.student_assignments_view, name='student_assignments'),
    path('assignments/review/', views.assignments_review_view, name='assignments_review'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment_view, name='submit_assignment'),
    path('assignments/submissions/<int:submission_id>/grade/', views.grade_submission_view, name='grade_submission'),

    # Faculty / Teachers Roster Module
    path('teachers/', views.teacher_list_view, name='teacher_list'),
    
    # Gamification Hub Module
    path('gamification/', views.gamification_hub_view, name='gamification_hub'),

    # Notifications Center Module
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='mark_notification_read'),

    # Parent-Teacher Meeting (PTM) Portal Module
    path('meetings/', views.ptm_list_view, name='ptm_list'),
    path('meetings/schedule/', views.ptm_schedule_view, name='ptm_schedule'),
    path('meetings/<int:pk>/status/', views.ptm_update_status_view, name='ptm_update_status'),

    # Performance Evaluation & Indicator Entry Hub
    path('performance/indicators/', views.indicators_entry_view, name='indicators_entry'),
    
    # Data Entry & Management
    path('marks/entry/', views.marks_entry_view, name='marks_entry'),
    path('attendance/mark/', views.attendance_entry_view, name='attendance_entry'),
    path('awards/', views.awards_management_view, name='awards_management'),
    path('awards/<int:pk>/approve/', views.approve_award_view, name='approve_award'),
    path('awards/<int:award_id>/certificate/', views.download_certificate_pdf_view, name='download_certificate_pdf'),
    
    # Analytics & Risk
    path('analytics/at-risk/', views.at_risk_monitoring_view, name='at_risk_monitoring'),
    path('analytics/class/', views.class_analytics_view, name='class_analytics'),
    
    # System Settings & Reports
    path('settings/', views.settings_view, name='settings'),
    path('import/', views.csv_import_view, name='csv_import'),
    path('reports/', views.report_center_view, name='report_center'),
    path('reports/pdf/<int:student_id>/', views.download_pdf_report_view, name='download_pdf_report'),
    path('reports/excel/', views.export_excel_report_view, name='export_excel_report'),

    # REST API & OpenAPI Swagger Docs
    path('api/', include(router.urls)),
    path('api/dashboard-summary/', api_views.dashboard_api_summary, name='api_dashboard_summary'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
