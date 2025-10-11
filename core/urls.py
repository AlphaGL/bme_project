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
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    
    # Admin Dashboard
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Staff Management
    path('admin/staff/', views.manage_staff, name='manage_staff'),
    path('admin/staff/add/', views.add_staff, name='add_staff'),
    path('admin/staff/edit/<int:pk>/', views.edit_staff, name='edit_staff'),
    path('admin/staff/delete/<int:pk>/', views.delete_staff, name='delete_staff'),
    
    # Exco Management
    path('admin/excos/', views.manage_excos, name='manage_excos'),
    path('admin/excos/add/', views.add_exco, name='add_exco'),
    path('admin/excos/edit/<int:pk>/', views.edit_exco, name='edit_exco'),
    path('admin/excos/delete/<int:pk>/', views.delete_exco, name='delete_exco'),
    
    # Past Questions Management
    path('admin/pastquestions/', views.manage_pastquestions, name='manage_pastquestions'),
    path('admin/pastquestions/add/', views.add_pastquestion, name='add_pastquestion'),
    path('admin/pastquestions/edit/<int:pk>/', views.edit_pastquestion, name='edit_pastquestion'),
    path('admin/pastquestions/delete/<int:pk>/', views.delete_pastquestion, name='delete_pastquestion'),
    
    # Library Management
    path('admin/library/', views.manage_library, name='manage_library'),
    path('admin/library/add/', views.add_library_resource, name='add_library_resource'),
    path('admin/library/edit/<int:pk>/', views.edit_library_resource, name='edit_library_resource'),
    path('admin/library/delete/<int:pk>/', views.delete_library_resource, name='delete_library_resource'),
    
    # Testimonials Management
    path('admin/testimonials/', views.manage_testimonials, name='manage_testimonials'),
    path('admin/testimonials/approve/<int:pk>/', views.approve_testimonial, name='approve_testimonial'),
    path('admin/testimonials/unapprove/<int:pk>/', views.unapprove_testimonial, name='unapprove_testimonial'),
    path('admin/testimonials/delete/<int:pk>/', views.delete_testimonial, name='delete_testimonial'),
    
    # Announcements Management
    path('admin/announcements/', views.manage_announcements, name='manage_announcements'),
    path('admin/announcements/add/', views.add_announcement, name='add_announcement'),
    path('admin/announcements/edit/<int:pk>/', views.edit_announcement, name='edit_announcement'),
    path('admin/announcements/delete/<int:pk>/', views.delete_announcement, name='delete_announcement'),
]