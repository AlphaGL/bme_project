# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public Pages
    path('', views.index, name='index'),
    path('virtual-tour/', views.virtual_tour, name='virtual_tour'),
    path('staff/', views.staff_list, name='staff_list'),
    path('excos/', views.exco_list, name='exco_list'),
    path('past-questions/', views.past_questions, name='past_questions'),
    path('library/', views.library, name='library'),
    path('submit-testimonial/', views.submit_testimonial, name='submit_testimonial'),
    
    # Student Portal
    path('student/register/', views.student_register, name='student_register'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/delete-account/', views.delete_student_account, name='delete_student_account'),
    
    # CGPA Calculator
    path('student/cgpa-calculator/', views.cgpa_calculator, name='cgpa_calculator'),
    path('student/semester/add/', views.add_semester, name='add_semester'),
    path('student/semester/<int:pk>/edit/', views.edit_semester, name='edit_semester'),
    path('student/semester/<int:pk>/delete/', views.delete_semester, name='delete_semester'),
    path('student/semester/<int:semester_id>/course/add/', views.add_course, name='add_course'),
    path('student/course/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('student/course/<int:pk>/delete/', views.delete_course, name='delete_course'),
    path('student/calculate-cgpa/', views.calculate_cgpa, name='calculate_cgpa'),
    path('student/cgpa-history/', views.cgpa_history, name='cgpa_history'),
    
    # Admin Authentication
    path('encrypted/admin/futobme/login/', views.admin_login, name='admin_login'),
    path('encrypted/admin/futobme/logout/', views.admin_logout, name='admin_logout'),
    
    # Admin Dashboard
    path('encrypted/admin/futobme/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Staff Management
    path('encrypted/admin/futobme/staff/', views.manage_staff, name='manage_staff'),
    path('encrypted/admin/futobme/staff/add/', views.add_staff, name='add_staff'),
    path('encrypted/admin/futobme/staff/edit/<int:pk>/', views.edit_staff, name='edit_staff'),
    path('encrypted/admin/futobme/staff/delete/<int:pk>/', views.delete_staff, name='delete_staff'),
    
    # Exco Management
    path('encrypted/admin/futobme/excos/', views.manage_excos, name='manage_excos'),
    path('encrypted/admin/futobme/excos/add/', views.add_exco, name='add_exco'),
    path('encrypted/admin/futobme/excos/edit/<int:pk>/', views.edit_exco, name='edit_exco'),
    path('encrypted/admin/futobme/excos/delete/<int:pk>/', views.delete_exco, name='delete_exco'),
    
    # Past Questions Management
    path('encrypted/admin/futobme/pastquestions/', views.manage_pastquestions, name='manage_pastquestions'),
    path('encrypted/admin/futobme/pastquestions/add/', views.add_pastquestion, name='add_pastquestion'),
    path('encrypted/admin/futobme/pastquestions/edit/<int:pk>/', views.edit_pastquestion, name='edit_pastquestion'),
    path('encrypted/admin/futobme/pastquestions/delete/<int:pk>/', views.delete_pastquestion, name='delete_pastquestion'),
    
    # Library Management
    path('encrypted/admin/futobme/library/', views.manage_library, name='manage_library'),
    path('encrypted/admin/futobme/library/add/', views.add_library_resource, name='add_library_resource'),
    path('encrypted/admin/futobme/library/edit/<int:pk>/', views.edit_library_resource, name='edit_library_resource'),
    path('encrypted/admin/futobme/library/delete/<int:pk>/', views.delete_library_resource, name='delete_library_resource'),
    
    # Testimonials Management
    path('encrypted/admin/futobme/testimonials/', views.manage_testimonials, name='manage_testimonials'),
    path('encrypted/admin/futobme/testimonials/approve/<int:pk>/', views.approve_testimonial, name='approve_testimonial'),
    path('encrypted/admin/futobme/testimonials/unapprove/<int:pk>/', views.unapprove_testimonial, name='unapprove_testimonial'),
    path('encrypted/admin/futobme/testimonials/delete/<int:pk>/', views.delete_testimonial, name='delete_testimonial'),
    
    # Announcements Management
    path('encrypted/admin/futobme/announcements/', views.manage_announcements, name='manage_announcements'),
    path('encrypted/admin/futobme/announcements/add/', views.add_announcement, name='add_announcement'),
    path('encrypted/admin/futobme/announcements/edit/<int:pk>/', views.edit_announcement, name='edit_announcement'),
    path('encrypted/admin/futobme/announcements/delete/<int:pk>/', views.delete_announcement, name='delete_announcement'),
    
    # ==================== DEPARTMENTAL DUES URLs ====================
    path('encrypted/admin/futobme/dues/', views.manage_departmental_dues, name='manage_departmental_dues'),
    path('encrypted/admin/futobme/dues/add/', views.add_departmental_dues, name='add_departmental_dues'),
    path('encrypted/admin/futobme/dues/edit/<int:pk>/', views.edit_departmental_dues, name='edit_departmental_dues'),
    path('encrypted/admin/futobme/dues/approve/<int:pk>/', views.approve_dues, name='approve_dues'),
    path('encrypted/admin/futobme/dues/delete/<int:pk>/', views.delete_departmental_dues, name='delete_departmental_dues'),
    
    # Student Receipt URLs
    path('student/my-receipt/', views.my_receipt, name='my_receipt'),
    path('student/print-receipt/', views.print_receipt, name='print_receipt'),
    
    # ==================== COURSE HANDBOOK URLs ====================
    path('encrypted/admin/futobme/handbook/', views.manage_course_handbook, name='manage_course_handbook'),
    path('encrypted/admin/futobme/handbook/add/', views.add_course_handbook, name='add_course_handbook'),
    path('encrypted/admin/futobme/handbook/edit/<int:pk>/', views.edit_course_handbook, name='edit_course_handbook'),
    path('encrypted/admin/futobme/handbook/delete/<int:pk>/', views.delete_course_handbook, name='delete_course_handbook'),
    
    # Public Course Handbook URL
    path('course-handbook/', views.view_course_handbook, name='view_course_handbook'),
    
    # ==================== TIMETABLE URLs ====================
    path('encrypted/admin/futobme/timetables/', views.manage_timetables, name='manage_timetables'),
    path('encrypted/admin/futobme/timetables/add/', views.add_timetable, name='add_timetable'),
    path('encrypted/admin/futobme/timetables/edit/<int:pk>/', views.edit_timetable, name='edit_timetable'),
    path('encrypted/admin/futobme/timetables/delete/<int:pk>/', views.delete_timetable, name='delete_timetable'),
    
    # Public Timetables URL
    path('timetables/', views.view_timetables, name='view_timetables'),
    
    # ==================== ACADEMIC CALENDAR URLs ====================
    path('encrypted/admin/futobme/calendars/', views.manage_calendars, name='manage_calendars'),
    path('encrypted/admin/futobme/calendars/add/', views.add_calendar, name='add_calendar'),
    path('encrypted/admin/futobme/calendars/edit/<int:pk>/', views.edit_calendar, name='edit_calendar'),
    path('encrypted/admin/futobme/calendars/delete/<int:pk>/', views.delete_calendar, name='delete_calendar'),
    
    # Public Academic Calendar URL
    path('academic-calendar/', views.view_calendar, name='view_calendar'),
]