# core/urls.py
from django.urls import path
from . import views
from django.views.generic import TemplateView

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
    path('student/registration-request/', views.registration_request, name='registration_request'),
    path('student/payment/', views.student_payment, name='student_payment'),
    path('student/payment/verify/', views.verify_payment, name='verify_payment'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/change-password/', views.change_password, name='change_password'),
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

    # Admin - Registration Requests Management
    path('encrypted/admin/futobme/registration-requests/', views.manage_registration_requests, name='manage_registration_requests'),
    path('encrypted/admin/futobme/registration-requests/approve/<int:pk>/', views.approve_registration_request, name='approve_registration_request'),
    path('encrypted/admin/futobme/registration-requests/reject/<int:pk>/', views.reject_registration_request, name='reject_registration_request'),
    
    # Admin - Registered Numbers Management
    path('encrypted/admin/futobme/registered-numbers/', views.manage_registered_numbers, name='manage_registered_numbers'),
    path('encrypted/admin/futobme/registered-numbers/add/', views.add_registered_number, name='add_registered_number'),
    path('encrypted/admin/futobme/registered-numbers/delete/<str:pk>/', views.delete_registered_number, name='delete_registered_number'),
    path('encrypted/admin/futobme/registered-numbers/bulk-import/', views.bulk_import_numbers, name='bulk_import_numbers'),
    
    # Admin - Payments Management
    path('encrypted/admin/futobme/payments/', views.manage_payments, name='manage_payments'),
    path('encrypted/admin/futobme/payments/<int:pk>/', views.view_payment_detail, name='view_payment_detail'),
    
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
    
    # ==================== PUBLIC RESEARCH URLs ====================
    path('research/', views.research_hub, name='research_hub'),
    path('research/team/<int:team_id>/', views.research_team_detail, name='research_team_detail'),
    path('research/team/<int:team_id>/join/', views.join_research_team, name='join_research_team'),
    path('research/article/<int:article_id>/', views.research_article_detail, name='research_article_detail'),
    path('research/article/<int:article_id>/like/', views.like_article, name='like_article'),
    path('research/article/<int:article_id>/contribute/', views.contribute_to_article, name='contribute_to_article'),
    
    # Guest Contributor URLs
    path('research/guest/choice/', views.guest_contributor_choice, name='guest_contributor_choice'),
    path('research/guest/register/', views.guest_contributor_register, name='guest_contributor_register'),
    path('research/guest/login/', views.guest_contributor_login, name='guest_contributor_login'),
    path('research/guest/logout/', views.guest_contributor_logout, name='guest_contributor_logout'),
    
    # Quiz URLs
    path('research/quizzes/', views.research_quizzes, name='research_quizzes'),
    path('research/quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('research/quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    
    # ==================== ADMIN RESEARCH MANAGEMENT URLs ====================
    # Research Teams
    path('encrypted/admin/futobme/research/teams/', views.manage_research_teams, name='manage_research_teams'),
    path('encrypted/admin/futobme/research/teams/add/', views.add_research_team, name='add_research_team'),
    path('encrypted/admin/futobme/research/teams/edit/<int:pk>/', views.edit_research_team, name='edit_research_team'),
    path('encrypted/admin/futobme/research/teams/delete/<int:pk>/', views.delete_research_team, name='delete_research_team'),
    
    # Research Articles
    path('encrypted/admin/futobme/research/articles/', views.manage_research_articles, name='manage_research_articles'),
    path('encrypted/admin/futobme/research/articles/add/', views.add_research_article, name='add_research_article'),
    path('encrypted/admin/futobme/research/articles/edit/<int:pk>/', views.edit_research_article, name='edit_research_article'),
    path('encrypted/admin/futobme/research/articles/delete/<int:pk>/', views.delete_research_article, name='delete_research_article'),
    
    # Contributions Management
    path('encrypted/admin/futobme/research/contributions/', views.manage_contributions, name='manage_contributions'),
    path('encrypted/admin/futobme/research/contributions/approve/<int:pk>/', views.approve_contribution, name='approve_contribution'),
    path('encrypted/admin/futobme/research/contributions/reject/<int:pk>/', views.reject_contribution, name='reject_contribution'),
    
    # Guest Contributors Management
    path('encrypted/admin/futobme/research/guests/', views.manage_guest_contributors, name='manage_guest_contributors'),
    path('encrypted/admin/futobme/research/guests/approve/<int:pk>/', views.approve_guest_contributor, name='approve_guest_contributor'),
    path('encrypted/admin/futobme/research/guests/reject/<int:pk>/', views.reject_guest_contributor, name='reject_guest_contributor'),
    
    # Quiz Management
    path('encrypted/admin/futobme/research/quizzes/', views.manage_research_quizzes, name='manage_research_quizzes'),
    path('encrypted/admin/futobme/research/quizzes/add/', views.add_research_quiz, name='add_research_quiz'),
    path('encrypted/admin/futobme/research/quizzes/edit/<int:pk>/', views.edit_research_quiz, name='edit_research_quiz'),
    path('encrypted/admin/futobme/research/quizzes/delete/<int:pk>/', views.delete_research_quiz, name='delete_research_quiz'),
    
    # Quiz Submissions Management
    path('encrypted/admin/futobme/research/submissions/', views.manage_quiz_submissions, name='manage_quiz_submissions'),
    path('encrypted/admin/futobme/research/submissions/award/<int:pk>/', views.award_quiz_submission, name='award_quiz_submission'),
    path('encrypted/admin/futobme/research/submissions/detail/<int:pk>/', views.view_quiz_submission_detail, name='view_quiz_submission_detail'),


    path('offline/', TemplateView.as_view(template_name='core/offline.html'), name='offline'),
    
    # PWA files - MUST be at root level
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('sw.js', views.service_worker, name='service_worker_alt'),  # Alternative path
    path('manifest.json', views.manifest_json, name='manifest'),


    # ==================== RESEARCH CLUB REGISTRATION URLs ====================
    path('research/club/register/', views.research_club_register, name='research_club_register'),
    path('research/club/status/', views.research_club_status, name='research_club_status'),
    
    # ==================== ADMIN - RESEARCH CLUB MANAGEMENT ====================
    path('encrypted/admin/futobme/research/club-registrations/', views.manage_research_registrations, name='manage_research_registrations'),
    path('encrypted/admin/futobme/research/club-registrations/verify/<int:pk>/', views.verify_research_payment, name='verify_research_payment'),
]