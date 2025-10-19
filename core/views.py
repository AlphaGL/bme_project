from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from .models import( Staff, Exco, PastQuestion, 
                    LibraryResource, Testimonial, Announcement, 
                    Student, Semester, Course, CGPACalculation, DepartmentalDues, 
                    CourseHandbook, Timetable, AcademicCalendar,ResearchTeam, ResearchArticle, GuestContributor, 
                     ResearchContribution, ResearchQuiz, QuizSubmission, 
                     TeamMembership, ArticleLike)
from .forms import (StaffForm, ExcoForm, PastQuestionForm, LibraryResourceForm, TestimonialForm, 
                    AnnouncementForm, StudentRegistrationForm, StudentLoginForm, 
                    StudentProfileForm, SemesterForm, CourseForm,  DepartmentalDuesForm,
                    CourseHandbookForm, TimetableForm, AcademicCalendarForm,ResearchTeamForm, ResearchArticleForm, GuestContributorForm,
                    GuestLoginForm, ResearchContributionForm, ResearchQuizForm,
                    QuizSubmissionForm, TeamJoinForm)
import json
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string



def custom_404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def custom_403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)

def custom_500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)

# Public Views
def index(request):
    # Get all data for busy homepage
    testimonials = Testimonial.objects.filter(is_approved=True)[:6]
    announcements = Announcement.objects.filter(is_active=True)[:5]
    recent_staff = Staff.objects.all()[:3]
    current_excos = Exco.objects.all()[:4]
    recent_resources = LibraryResource.objects.all()[:6]
    recent_questions = PastQuestion.objects.all()[:5]
    
    # Statistics for homepage
    stats = {
        'total_staff': Staff.objects.count(),
        'total_students': 500,  # You can make this dynamic later
        'total_resources': LibraryResource.objects.count(),
        'total_questions': PastQuestion.objects.count(),
    }
    
    # Questions by level for chart
    questions_by_level = PastQuestion.objects.values('level').annotate(count=Count('id'))
    
    return render(request, 'core/index.html', {
        'testimonials': testimonials,
        'announcements': announcements,
        'recent_staff': recent_staff,
        'current_excos': current_excos,
        'recent_resources': recent_resources,
        'recent_questions': recent_questions,
        'stats': stats,
        'questions_by_level': questions_by_level,
    })

def virtual_tour(request):
    """Virtual tour page with video placeholders"""
    tour_locations = [
        {
            'title': 'Department Building',
            'description': 'Take a virtual tour of our state-of-the-art Biomedical Engineering department building.',
            'video_id': 'dept_building',
            'thumbnail': 'https://via.placeholder.com/800x450/0d6efd/ffffff?text=Department+Building'
        },
        {
            'title': 'Lecture Halls',
            'description': 'Modern, well-equipped lecture halls designed for optimal learning experience.',
            'video_id': 'lecture_halls',
            'thumbnail': 'https://via.placeholder.com/800x450/198754/ffffff?text=Lecture+Halls'
        },
        {
            'title': 'Laboratory Facilities',
            'description': 'Advanced laboratories with cutting-edge equipment for practical sessions.',
            'video_id': 'laboratories',
            'thumbnail': 'https://via.placeholder.com/800x450/dc3545/ffffff?text=Laboratory+Facilities'
        },
        {
            'title': 'Research Centers',
            'description': 'Dedicated research facilities for innovation and development in biomedical engineering.',
            'video_id': 'research_center',
            'thumbnail': 'https://via.placeholder.com/800x450/ffc107/000000?text=Research+Centers'
        },
        {
            'title': 'Student Common Room',
            'description': 'Comfortable spaces for students to relax, study, and collaborate.',
            'video_id': 'common_room',
            'thumbnail': 'https://via.placeholder.com/800x450/0dcaf0/000000?text=Student+Common+Room'
        },
        {
            'title': 'Medical Equipment Lab',
            'description': 'Hands-on training with real medical equipment and devices.',
            'video_id': 'medical_equipment',
            'thumbnail': 'https://via.placeholder.com/800x450/6c757d/ffffff?text=Medical+Equipment+Lab'
        },
    ]
    
    return render(request, 'core/virtual_tour.html', {
        'tour_locations': tour_locations
    })

def staff_list(request):
    staff = Staff.objects.all()
    return render(request, 'core/staff.html', {'staff': staff})

def exco_list(request):
    excos = Exco.objects.all()
    return render(request, 'core/excos.html', {'excos': excos})

def past_questions(request):
    level = request.GET.get('level', '')
    semester = request.GET.get('semester', '')
    year = request.GET.get('year', '')
    
    questions = PastQuestion.objects.all()
    
    if level:
        questions = questions.filter(level=level)
    if semester:
        questions = questions.filter(semester=semester)
    if year:
        questions = questions.filter(year=year)
    
    years = PastQuestion.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    return render(request, 'core/past_questions.html', {
        'questions': questions,
        'years': years,
        'selected_level': level,
        'selected_semester': semester,
        'selected_year': year
    })

def library(request):
    category = request.GET.get('category', '')
    level = request.GET.get('level', '')
    
    resources = LibraryResource.objects.all()
    
    if category:
        resources = resources.filter(category=category)
    if level:
        resources = resources.filter(level=level)
    
    return render(request, 'core/library.html', {
        'resources': resources,
        'selected_category': category,
        'selected_level': level
    })

def submit_testimonial(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you! Your testimonial has been submitted for review.')
            return redirect('index')
    else:
        form = TestimonialForm()
    return render(request, 'core/submit_testimonial.html', {'form': form})

@login_required
def add_library_resource(request):
    if request.method == 'POST':
        form = LibraryResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, 'Library resource added successfully!')
            return redirect('manage_library')
    else:
        form = LibraryResourceForm()
    return render(request, 'core/admin/library_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_library_resource(request, pk):
    resource = get_object_or_404(LibraryResource, pk=pk)
    if request.method == 'POST':
        form = LibraryResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Library resource updated successfully!')
            return redirect('manage_library')
    else:
        form = LibraryResourceForm(instance=resource)
    return render(request, 'core/admin/library_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_library_resource(request, pk):
    resource = get_object_or_404(LibraryResource, pk=pk)
    if request.method == 'POST':
        resource.delete()
        messages.success(request, 'Library resource deleted successfully!')
        return redirect('manage_library')
    return render(request, 'core/admin/confirm_delete.html', {'object': resource, 'type': 'Library Resource'})

# Testimonials Management
@login_required
def manage_testimonials(request):
    testimonials = Testimonial.objects.all()
    return render(request, 'core/admin/manage_testimonials.html', {'testimonials': testimonials})

@login_required
def approve_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.is_approved = True
    testimonial.save()
    messages.success(request, 'Testimonial approved!')
    return redirect('manage_testimonials')

@login_required
def unapprove_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.is_approved = False
    testimonial.save()
    messages.success(request, 'Testimonial unapproved!')
    return redirect('manage_testimonials')

@login_required
def delete_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == 'POST':
        testimonial.delete()
        messages.success(request, 'Testimonial deleted successfully!')
        return redirect('manage_testimonials')
    return render(request, 'core/admin/confirm_delete.html', {'object': testimonial, 'type': 'Testimonial'})

# Announcements Management
@login_required
def manage_announcements(request):
    announcements = Announcement.objects.all()
    return render(request, 'core/admin/manage_announcements.html', {'announcements': announcements})

@login_required
def add_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, 'Announcement added successfully!')
            return redirect('manage_announcements')
    else:
        form = AnnouncementForm()
    return render(request, 'core/admin/announcement_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated successfully!')
            return redirect('manage_announcements')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'core/admin/announcement_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
        return redirect('manage_announcements')
    return render(request, 'core/admin/confirm_delete.html', {'object': announcement, 'type': 'Announcement'})

# Admin Authentication
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'core/admin/login.html')

@login_required
def admin_logout(request):
    logout(request)
    return redirect('index')

# Admin Dashboard
@login_required
def admin_dashboard(request):
    stats = {
        'staff_count': Staff.objects.count(),
        'excos_count': Exco.objects.count(),
        'past_questions_count': PastQuestion.objects.count(),
        'library_count': LibraryResource.objects.count(),
        'testimonials_pending': Testimonial.objects.filter(is_approved=False).count(),
        'announcements_active': Announcement.objects.filter(is_active=True).count(),
    }
    return render(request, 'core/admin/dashboard.html', {'stats': stats})

# Staff Management
@login_required
def manage_staff(request):
    staff = Staff.objects.all()
    return render(request, 'core/admin/manage_staff.html', {'staff': staff})

@login_required
def add_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member added successfully!')
            return redirect('manage_staff')
    else:
        form = StaffForm()
    return render(request, 'core/admin/staff_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_staff(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member updated successfully!')
            return redirect('manage_staff')
    else:
        form = StaffForm(instance=staff)
    return render(request, 'core/admin/staff_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_staff(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff member deleted successfully!')
        return redirect('manage_staff')
    return render(request, 'core/admin/confirm_delete.html', {'object': staff, 'type': 'Staff'})

# Exco Management
@login_required
def manage_excos(request):
    excos = Exco.objects.all()
    return render(request, 'core/admin/manage_excos.html', {'excos': excos})

@login_required
def add_exco(request):
    if request.method == 'POST':
        form = ExcoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exco added successfully!')
            return redirect('manage_excos')
    else:
        form = ExcoForm()
    return render(request, 'core/admin/exco_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_exco(request, pk):
    exco = get_object_or_404(Exco, pk=pk)
    if request.method == 'POST':
        form = ExcoForm(request.POST, request.FILES, instance=exco)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exco updated successfully!')
            return redirect('manage_excos')
    else:
        form = ExcoForm(instance=exco)
    return render(request, 'core/admin/exco_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_exco(request, pk):
    exco = get_object_or_404(Exco, pk=pk)
    if request.method == 'POST':
        exco.delete()
        messages.success(request, 'Exco deleted successfully!')
        return redirect('manage_excos')
    return render(request, 'core/admin/confirm_delete.html', {'object': exco, 'type': 'Exco'})

# Past Questions Management
@login_required
def manage_pastquestions(request):
    questions = PastQuestion.objects.all()
    return render(request, 'core/admin/manage_pastquestions.html', {'questions': questions})

@login_required
def add_pastquestion(request):
    if request.method == 'POST':
        form = PastQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.uploaded_by = request.user
            question.save()
            messages.success(request, 'Past question added successfully!')
            return redirect('manage_pastquestions')
    else:
        form = PastQuestionForm()
    return render(request, 'core/admin/pastquestion_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_pastquestion(request, pk):
    question = get_object_or_404(PastQuestion, pk=pk)
    if request.method == 'POST':
        form = PastQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Past question updated successfully!')
            return redirect('manage_pastquestions')
    else:
        form = PastQuestionForm(instance=question)
    return render(request, 'core/admin/pastquestion_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_pastquestion(request, pk):
    question = get_object_or_404(PastQuestion, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Past question deleted successfully!')
        return redirect('manage_pastquestions')
    return render(request, 'core/admin/confirm_delete.html', {'object': question, 'type': 'Past Question'})

# Library Management
@login_required
def manage_library(request):
    resources = LibraryResource.objects.all()
    return render(request, 'core/admin/manage_library.html', {'resources': resources})

# STUDENT AUTHENTICATION
def student_register(request):
    if request.session.get('student_reg_number'):
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            student = form.save()
            request.session['student_reg_number'] = student.reg_number
            messages.success(request, f'Welcome {student.full_name}! Your account has been created successfully.')
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'core/student/register.html', {'form': form})


def student_login(request):
    if request.session.get('student_reg_number'):
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            reg_number = form.cleaned_data['reg_number']
            try:
                student = Student.objects.get(reg_number=reg_number)
                request.session['student_reg_number'] = student.reg_number
                messages.success(request, f'Welcome back, {student.full_name}!')
                return redirect('student_dashboard')
            except Student.DoesNotExist:
                messages.error(request, 'Invalid registration number. Please check and try again.')
    else:
        form = StudentLoginForm()
    
    return render(request, 'core/student/login.html', {'form': form})


def student_logout(request):
    if 'student_reg_number' in request.session:
        del request.session['student_reg_number']
    messages.success(request, 'You have been logged out successfully.')
    return redirect('student_login')


# STUDENT DECORATOR
def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('student_reg_number'):
            messages.error(request, 'Please login to access the student portal.')
            return redirect('student_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# STUDENT DASHBOARD
@student_required
def student_dashboard(request):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    # Get all semesters and their GPAs
    semesters = student.semesters.all()
    semester_data = []
    total_credits = 0
    total_points = 0
    
    for semester in semesters:
        gpa = semester.calculate_gpa()
        courses = semester.courses.all()
        semester_credits = sum(c.credit_unit for c in courses)
        semester_points = sum(c.credit_unit * c.grade_point for c in courses)
        
        total_credits += semester_credits
        total_points += semester_points
        
        semester_data.append({
            'semester': semester,
            'gpa': gpa,
            'courses_count': courses.count(),
            'credits': semester_credits
        })
    
    # Calculate CGPA
    cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    
    # Get latest CGPA calculation
    latest_cgpa = student.cgpa_calculations.first()
    
    # Recent announcements
    announcements = Announcement.objects.filter(is_active=True)[:3]
    
    context = {
        'student': student,
        'semesters': semester_data,
        'cgpa': cgpa,
        'total_credits': total_credits,
        'latest_cgpa': latest_cgpa,
        'announcements': announcements,
    }
    
    return render(request, 'core/student/dashboard.html', context)


# PROFILE MANAGEMENT
@student_required
def student_profile(request):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=student)
    
    return render(request, 'core/student/profile.html', {'form': form, 'student': student})


@student_required
def delete_student_account(request):
    if request.method == 'POST':
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        student.delete()
        del request.session['student_reg_number']
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('index')
    
    return render(request, 'core/student/confirm_delete_account.html')


# CGPA CALCULATOR
@student_required
def cgpa_calculator(request):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    semesters = student.semesters.all().prefetch_related('courses')
    
    return render(request, 'core/student/cgpa_calculator.html', {
        'student': student,
        'semesters': semesters
    })


@student_required
def add_semester(request):
    if request.method == 'POST':
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save(commit=False)
            semester.student = student
            semester.save()
            messages.success(request, f'Semester "{semester.name}" added successfully!')
            return redirect('cgpa_calculator')
    else:
        form = SemesterForm()
    
    return render(request, 'core/student/semester_form.html', {'form': form, 'action': 'Add'})


@student_required
def edit_semester(request, pk):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    semester = get_object_or_404(Semester, pk=pk, student=student)
    
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester updated successfully!')
            return redirect('cgpa_calculator')
    else:
        form = SemesterForm(instance=semester)
    
    return render(request, 'core/student/semester_form.html', {'form': form, 'action': 'Edit'})


@student_required
def delete_semester(request, pk):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    semester = get_object_or_404(Semester, pk=pk, student=student)
    
    if request.method == 'POST':
        semester_name = semester.name
        semester.delete()
        messages.success(request, f'Semester "{semester_name}" deleted successfully!')
        return redirect('cgpa_calculator')
    
    return render(request, 'core/student/confirm_delete.html', {
        'object': semester,
        'type': 'Semester',
        'cancel_url': 'cgpa_calculator'
    })


@student_required
def add_course(request, semester_id):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    semester = get_object_or_404(Semester, pk=semester_id, student=student)
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.semester = semester
            course.save()
            messages.success(request, f'Course "{course.course_code}" added successfully!')
            return redirect('cgpa_calculator')
    else:
        form = CourseForm()
    
    return render(request, 'core/student/course_form.html', {
        'form': form,
        'semester': semester,
        'action': 'Add'
    })


@student_required
def edit_course(request, pk):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    course = get_object_or_404(Course, pk=pk, semester__student=student)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('cgpa_calculator')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'core/student/course_form.html', {
        'form': form,
        'semester': course.semester,
        'action': 'Edit'
    })


@student_required
def delete_course(request, pk):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    course = get_object_or_404(Course, pk=pk, semester__student=student)
    
    if request.method == 'POST':
        course_name = f"{course.course_code} - {course.course_name}"
        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully!')
        return redirect('cgpa_calculator')
    
    return render(request, 'core/student/confirm_delete.html', {
        'object': course,
        'type': 'Course',
        'cancel_url': 'cgpa_calculator'
    })


@student_required
def calculate_cgpa(request):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    semesters = student.semesters.all()
    total_credits = 0
    total_points = 0
    semester_results = []
    
    for semester in semesters:
        courses = semester.courses.all()
        semester_credits = sum(c.credit_unit for c in courses)
        semester_points = sum(c.credit_unit * c.grade_point for c in courses)
        gpa = round(semester_points / semester_credits, 2) if semester_credits > 0 else 0.0
        
        total_credits += semester_credits
        total_points += semester_points
        
        semester_results.append({
            'name': semester.name,
            'gpa': gpa,
            'credits': semester_credits,
            'courses': [{
                'code': c.course_code,
                'name': c.course_name,
                'credits': c.credit_unit,
                'grade': c.get_grade_letter(),
                'grade_point': c.grade_point
            } for c in courses]
        })
    
    cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    
    # Save CGPA calculation
    CGPACalculation.objects.create(
        student=student,
        cgpa=cgpa,
        total_credit_units=total_credits,
        total_grade_points=total_points
    )
    
    context = {
        'student': student,
        'cgpa': cgpa,
        'total_credits': total_credits,
        'total_points': total_points,
        'semester_results': semester_results,
    }
    
    return render(request, 'core/student/cgpa_result.html', context)


@student_required
def cgpa_history(request):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    calculations = student.cgpa_calculations.all()[:10]  # Last 10 calculations
    
    return render(request, 'core/student/cgpa_history.html', {
        'student': student,
        'calculations': calculations
    })


# ==================== DEPARTMENTAL DUES VIEWS ====================

@login_required
def manage_departmental_dues(request):
    """Admin view to manage all departmental dues"""
    dues = DepartmentalDues.objects.all().select_related('student', 'approved_by')

    # Compute summary statistics
    total_count = dues.count()
    approved_count = dues.filter(is_approved=True).count()
    pending_count = dues.filter(is_approved=False).count()

    context = {
        'dues': dues,
        'total_count': total_count,
        'approved_count': approved_count,
        'pending_count': pending_count,
    }
    return render(request, 'core/admin/manage_dues.html', context)


@login_required
def add_departmental_dues(request):
    """Admin adds departmental dues for a student"""
    if request.method == 'POST':
        form = DepartmentalDuesForm(request.POST)
        if form.is_valid():
            dues = form.save(commit=False)
            if dues.is_approved:
                dues.approved_by = request.user
                dues.approved_at = timezone.now()
            dues.save()
            messages.success(request, 'Departmental dues added successfully!')
            return redirect('manage_departmental_dues')
    else:
        form = DepartmentalDuesForm()
    return render(request, 'core/admin/dues_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_departmental_dues(request, pk):
    """Admin edits departmental dues"""
    dues = get_object_or_404(DepartmentalDues, pk=pk)
    if request.method == 'POST':
        form = DepartmentalDuesForm(request.POST, instance=dues)
        if form.is_valid():
            dues = form.save(commit=False)
            if dues.is_approved and not dues.approved_at:
                dues.approved_by = request.user
                dues.approved_at = timezone.now()
            dues.save()
            messages.success(request, 'Departmental dues updated successfully!')
            return redirect('manage_departmental_dues')
    else:
        form = DepartmentalDuesForm(instance=dues)
    return render(request, 'core/admin/dues_form.html', {'form': form, 'action': 'Edit'})


@login_required
def approve_dues(request, pk):
    """Admin approves departmental dues"""
    dues = get_object_or_404(DepartmentalDues, pk=pk)
    dues.is_approved = True
    dues.approved_by = request.user
    dues.approved_at = timezone.now()
    dues.save()
    messages.success(request, f'Dues for {dues.student.full_name} approved successfully!')
    return redirect('manage_departmental_dues')


@login_required
def delete_departmental_dues(request, pk):
    """Admin deletes departmental dues"""
    dues = get_object_or_404(DepartmentalDues, pk=pk)
    if request.method == 'POST':
        dues.delete()
        messages.success(request, 'Departmental dues deleted successfully!')
        return redirect('manage_departmental_dues')
    return render(request, 'core/admin/confirm_delete.html', {'object': dues, 'type': 'Departmental Dues'})


@student_required
def my_receipt(request):
    """Student views their departmental receipt"""
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    try:
        dues = DepartmentalDues.objects.get(student=student)
    except DepartmentalDues.DoesNotExist:
        dues = None
    
    return render(request, 'core/student/my_receipt.html', {
        'student': student,
        'dues': dues
    })


@student_required
def print_receipt(request):
    """Student prints their receipt"""
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    try:
        dues = DepartmentalDues.objects.get(student=student, is_approved=True)
    except DepartmentalDues.DoesNotExist:
        messages.error(request, 'Your departmental dues have not been approved yet.')
        return redirect('my_receipt')
    
    return render(request, 'core/student/print_receipt.html', {
        'student': student,
        'dues': dues
    })


# ==================== COURSE HANDBOOK VIEWS ====================

@login_required
def manage_course_handbook(request):
    """Admin manages course handbook"""
    courses = CourseHandbook.objects.all()
    
    # Group by level and semester
    grouped_courses = {}
    for course in courses:
        key = f"{course.level}L {course.semester}"
        if key not in grouped_courses:
            grouped_courses[key] = []
        grouped_courses[key].append(course)
    
    return render(request, 'core/admin/manage_handbook.html', {
        'grouped_courses': grouped_courses
    })


@login_required
def add_course_handbook(request):
    """Admin adds course to handbook"""
    if request.method == 'POST':
        form = CourseHandbookForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.uploaded_by = request.user
            course.save()
            messages.success(request, 'Course added to handbook successfully!')
            return redirect('manage_course_handbook')
    else:
        form = CourseHandbookForm()
    return render(request, 'core/admin/handbook_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_course_handbook(request, pk):
    """Admin edits course in handbook"""
    course = get_object_or_404(CourseHandbook, pk=pk)
    if request.method == 'POST':
        form = CourseHandbookForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('manage_course_handbook')
    else:
        form = CourseHandbookForm(instance=course)
    return render(request, 'core/admin/handbook_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_course_handbook(request, pk):
    """Admin deletes course from handbook"""
    course = get_object_or_404(CourseHandbook, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('manage_course_handbook')
    return render(request, 'core/admin/confirm_delete.html', {'object': course, 'type': 'Course'})


def view_course_handbook(request):
    """Public/Student view of course handbook"""
    level = request.GET.get('level', '100')
    semester = request.GET.get('semester', 'First')
    
    courses = CourseHandbook.objects.filter(level=level, semester=semester)
    
    # Calculate total credit units
    total_credits = sum(course.credit_unit for course in courses)
    
    return render(request, 'core/course_handbook.html', {
        'courses': courses,
        'selected_level': level,
        'selected_semester': semester,
        'total_credits': total_credits
    })


# ==================== TIMETABLE VIEWS ====================

@login_required
def manage_timetables(request):
    """Admin manages timetables"""
    timetables = Timetable.objects.all()
    return render(request, 'core/admin/manage_timetables.html', {'timetables': timetables})


@login_required
def add_timetable(request):
    """Admin adds timetable"""
    if request.method == 'POST':
        form = TimetableForm(request.POST, request.FILES)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.uploaded_by = request.user
            timetable.save()
            messages.success(request, 'Timetable uploaded successfully!')
            return redirect('manage_timetables')
    else:
        form = TimetableForm()
    return render(request, 'core/admin/timetable_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_timetable(request, pk):
    """Admin edits timetable"""
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        form = TimetableForm(request.POST, request.FILES, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timetable updated successfully!')
            return redirect('manage_timetables')
    else:
        form = TimetableForm(instance=timetable)
    return render(request, 'core/admin/timetable_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_timetable(request, pk):
    """Admin deletes timetable"""
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        timetable.delete()
        messages.success(request, 'Timetable deleted successfully!')
        return redirect('manage_timetables')
    return render(request, 'core/admin/confirm_delete.html', {'object': timetable, 'type': 'Timetable'})


def view_timetables(request):
    """Public/Student view of timetables"""
    timetable_type = request.GET.get('type', 'Exam')
    level = request.GET.get('level', 'All')
    
    timetables = Timetable.objects.filter(is_active=True, timetable_type=timetable_type)
    if level != 'All':
        timetables = timetables.filter(level__in=[level, 'All'])
    
    return render(request, 'core/timetables.html', {
        'timetables': timetables,
        'selected_type': timetable_type,
        'selected_level': level
    })


# ==================== ACADEMIC CALENDAR VIEWS ====================

@login_required
def manage_calendars(request):
    """Admin manages academic calendars"""
    calendars = AcademicCalendar.objects.all()
    return render(request, 'core/admin/manage_calendars.html', {'calendars': calendars})


@login_required
def add_calendar(request):
    """Admin adds academic calendar"""
    if request.method == 'POST':
        form = AcademicCalendarForm(request.POST, request.FILES)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.uploaded_by = request.user
            calendar.save()
            messages.success(request, 'Academic calendar uploaded successfully!')
            return redirect('manage_calendars')
    else:
        form = AcademicCalendarForm()
    return render(request, 'core/admin/calendar_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_calendar(request, pk):
    """Admin edits academic calendar"""
    calendar = get_object_or_404(AcademicCalendar, pk=pk)
    if request.method == 'POST':
        form = AcademicCalendarForm(request.POST, request.FILES, instance=calendar)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic calendar updated successfully!')
            return redirect('manage_calendars')
    else:
        form = AcademicCalendarForm(instance=calendar)
    return render(request, 'core/admin/calendar_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_calendar(request, pk):
    """Admin deletes academic calendar"""
    calendar = get_object_or_404(AcademicCalendar, pk=pk)
    if request.method == 'POST':
        calendar.delete()
        messages.success(request, 'Academic calendar deleted successfully!')
        return redirect('manage_calendars')
    return render(request, 'core/admin/confirm_delete.html', {'object': calendar, 'type': 'Academic Calendar'})


def view_calendar(request):
    """Public/Student view of academic calendar"""
    calendar = AcademicCalendar.objects.filter(is_active=True).first()
    all_calendars = AcademicCalendar.objects.all()[:5]  # Show last 5
    
    return render(request, 'core/academic_calendar.html', {
        'calendar': calendar,
        'all_calendars': all_calendars
    })


# ==================== PUBLIC RESEARCH VIEWS ====================

def research_hub(request):
    """Main research hub showcasing all teams and recent activity"""
    teams = ResearchTeam.objects.filter(is_active=True)
    published_articles = ResearchArticle.objects.filter(status='Published')[:6]
    active_quizzes = ResearchQuiz.objects.filter(is_active=True)[:5]
    
    # Top contributors
    from django.db.models import Count
    top_contributors = ResearchContribution.objects.filter(
        is_approved=True
    ).values(
        'student_contributor__full_name',
        'student_contributor__reg_number'
    ).annotate(
        contribution_count=Count('id')
    ).order_by('-contribution_count')[:10]
    
    context = {
        'teams': teams,
        'published_articles': published_articles,
        'active_quizzes': active_quizzes,
        'top_contributors': top_contributors,
        'total_teams': teams.count(),
        'total_articles': ResearchArticle.objects.count(),
        'total_contributions': ResearchContribution.objects.filter(is_approved=True).count(),
    }
    return render(request, 'core/research/hub.html', context)


def research_team_detail(request, team_id):
    """Detailed view of a research team"""
    team = get_object_or_404(ResearchTeam, id=team_id)
    articles = team.articles.all()
    members = team.members.select_related('student').all()
    
    # Check if current user is a member
    is_member = False
    if request.session.get('student_reg_number'):
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        is_member = TeamMembership.objects.filter(team=team, student=student).exists()
    
    context = {
        'team': team,
        'articles': articles,
        'members': members,
        'is_member': is_member,
        'can_join': team.get_member_count() < team.max_members,
    }
    return render(request, 'core/research/team_detail.html', context)


def join_research_team(request, team_id):
    """Student joins a research team"""
    if not request.session.get('student_reg_number'):
        messages.error(request, 'Please login to join a research team.')
        return redirect('student_login')
    
    team = get_object_or_404(ResearchTeam, id=team_id)
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    # Check if already a member
    if TeamMembership.objects.filter(team=team, student=student).exists():
        messages.warning(request, 'You are already a member of this team!')
        return redirect('research_team_detail', team_id=team_id)
    
    # Check if team is full
    if team.get_member_count() >= team.max_members:
        messages.error(request, 'This team is currently full.')
        return redirect('research_team_detail', team_id=team_id)
    
    if request.method == 'POST':
        form = TeamJoinForm(request.POST)
        if form.is_valid():
            TeamMembership.objects.create(
                team=team,
                student=student,
                role=form.cleaned_data.get('role', 'Member')
            )
            messages.success(request, f'Welcome to {team.name}!')
            return redirect('research_team_detail', team_id=team_id)
    else:
        form = TeamJoinForm()
    
    return render(request, 'core/research/join_team.html', {'form': form, 'team': team})


def research_article_detail(request, article_id):
    """View a complete research article with all approved contributions"""
    article = get_object_or_404(ResearchArticle, id=article_id)
    contributions = article.get_approved_contributions()
    
    # Increment view count
    article.views_count += 1
    article.save(update_fields=['views_count'])
    
    # Check if student has liked this article
    has_liked = False
    if request.session.get('student_reg_number'):
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        has_liked = ArticleLike.objects.filter(article=article, student=student).exists()
    
    context = {
        'article': article,
        'contributions': contributions,
        'has_liked': has_liked,
    }
    return render(request, 'core/research/article_detail.html', context)


def like_article(request, article_id):
    """Toggle like on an article"""
    if not request.session.get('student_reg_number'):
        messages.error(request, 'Please login to like articles.')
        return redirect('student_login')
    
    article = get_object_or_404(ResearchArticle, id=article_id)
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    like, created = ArticleLike.objects.get_or_create(article=article, student=student)
    
    if not created:
        like.delete()
        article.likes_count -= 1
        messages.info(request, 'Article unliked.')
    else:
        article.likes_count += 1
        messages.success(request, 'Article liked!')
    
    article.save(update_fields=['likes_count'])
    return redirect('research_article_detail', article_id=article_id)


# ==================== CONTRIBUTION VIEWS ====================

def contribute_to_article(request, article_id):
    """Contribute to a research article"""
    article = get_object_or_404(ResearchArticle, id=article_id)
    
    # Determine contributor type
    contributor_type = None
    student_contributor = None
    guest_contributor = None
    
    if request.session.get('student_reg_number'):
        reg_number = request.session.get('student_reg_number')
        student_contributor = Student.objects.get(reg_number=reg_number)
        contributor_type = 'student'
        
        # Check if student is a team member
        if not TeamMembership.objects.filter(team=article.team, student=student_contributor).exists():
            messages.error(request, 'You must be a team member to contribute to this article.')
            return redirect('research_article_detail', article_id=article_id)
    
    elif request.session.get('guest_contributor_id'):
        guest_id = request.session.get('guest_contributor_id')
        guest_contributor = GuestContributor.objects.get(id=guest_id, is_approved=True)
        contributor_type = 'guest'
    
    else:
        messages.error(request, 'Please login or register as a guest contributor.')
        return redirect('guest_contributor_choice')
    
    if request.method == 'POST':
        form = ResearchContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.article = article
            
            if contributor_type == 'student':
                contribution.student_contributor = student_contributor
            else:
                contribution.guest_contributor = guest_contributor
            
            contribution.save()
            messages.success(request, 'Your contribution has been submitted for review!')
            return redirect('research_article_detail', article_id=article_id)
    else:
        form = ResearchContributionForm()
    
    context = {
        'form': form,
        'article': article,
        'contributor_type': contributor_type,
    }
    return render(request, 'core/research/contribute.html', context)


# ==================== GUEST CONTRIBUTOR VIEWS ====================

def guest_contributor_choice(request):
    """Guest contributor login or register choice"""
    return render(request, 'core/research/guest_choice.html')


def guest_contributor_register(request):
    """Register as a guest contributor"""
    if request.method == 'POST':
        form = GuestContributorForm(request.POST)
        if form.is_valid():
            guest = form.save()
            messages.success(request, 
                'Registration successful! Your application is pending admin approval. '
                'You will be notified via email once approved.')
            return redirect('research_hub')
    else:
        form = GuestContributorForm()
    
    return render(request, 'core/research/guest_register.html', {'form': form})


def guest_contributor_login(request):
    """Login for approved guest contributors"""
    if request.method == 'POST':
        form = GuestLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                guest = GuestContributor.objects.get(email=email)
                if not guest.is_approved:
                    messages.error(request, 'Your account is pending approval.')
                    return redirect('guest_contributor_login')
                
                if guest.check_password(password):
                    request.session['guest_contributor_id'] = guest.id
                    messages.success(request, f'Welcome back, {guest.full_name}!')
                    return redirect('research_hub')
                else:
                    messages.error(request, 'Invalid password.')
            except GuestContributor.DoesNotExist:
                messages.error(request, 'Email not found. Please register first.')
    else:
        form = GuestLoginForm()
    
    return render(request, 'core/research/guest_login.html', {'form': form})


def guest_contributor_logout(request):
    """Logout guest contributor"""
    if 'guest_contributor_id' in request.session:
        del request.session['guest_contributor_id']
    messages.success(request, 'You have been logged out successfully.')
    return redirect('research_hub')


# ==================== QUIZ VIEWS ====================

def research_quizzes(request):
    """View all active research quizzes"""
    quizzes = ResearchQuiz.objects.filter(is_active=True).order_by('-created_at')
    
    # Get user's submissions if logged in
    user_submissions = []
    if request.session.get('student_reg_number'):
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        user_submissions = QuizSubmission.objects.filter(
            student_submitter=student
        ).values_list('quiz_id', flat=True)
    
    context = {
        'quizzes': quizzes,
        'user_submissions': user_submissions,
    }
    return render(request, 'core/research/quizzes.html', context)


def quiz_detail(request, quiz_id):
    """View quiz details and submit solution"""
    quiz = get_object_or_404(ResearchQuiz, id=quiz_id)
    submissions = quiz.submissions.filter(is_awarded=True).order_by('-awarded_at')[:5]
    
    # Check if user has already submitted
    has_submitted = False
    user_submission = None
    
    if request.session.get('student_reg_number'):
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        user_submission = QuizSubmission.objects.filter(
            quiz=quiz, student_submitter=student
        ).first()
        has_submitted = user_submission is not None
    elif request.session.get('guest_contributor_id'):
        guest_id = request.session.get('guest_contributor_id')
        guest = GuestContributor.objects.get(id=guest_id)
        user_submission = QuizSubmission.objects.filter(
            quiz=quiz, guest_submitter=guest
        ).first()
        has_submitted = user_submission is not None
    
    context = {
        'quiz': quiz,
        'submissions': submissions,
        'has_submitted': has_submitted,
        'user_submission': user_submission,
    }
    return render(request, 'core/research/quiz_detail.html', context)


def submit_quiz(request, quiz_id):
    """Submit solution to a quiz"""
    quiz = get_object_or_404(ResearchQuiz, id=quiz_id)
    
    # Check if quiz is still active
    if not quiz.is_active:
        messages.error(request, 'This quiz is no longer active.')
        return redirect('quiz_detail', quiz_id=quiz_id)
    
    # Determine submitter
    student_submitter = None
    guest_submitter = None
    
    if request.session.get('student_reg_number'):
        reg_number = request.session.get('student_reg_number')
        student_submitter = Student.objects.get(reg_number=reg_number)
        
        # Check if already submitted
        if QuizSubmission.objects.filter(quiz=quiz, student_submitter=student_submitter).exists():
            messages.warning(request, 'You have already submitted a solution to this quiz.')
            return redirect('quiz_detail', quiz_id=quiz_id)
    
    elif request.session.get('guest_contributor_id'):
        guest_id = request.session.get('guest_contributor_id')
        guest_submitter = GuestContributor.objects.get(id=guest_id, is_approved=True)
        
        if QuizSubmission.objects.filter(quiz=quiz, guest_submitter=guest_submitter).exists():
            messages.warning(request, 'You have already submitted a solution to this quiz.')
            return redirect('quiz_detail', quiz_id=quiz_id)
    
    else:
        messages.error(request, 'Please login to submit a solution.')
        return redirect('guest_contributor_choice')
    
    if request.method == 'POST':
        form = QuizSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.quiz = quiz
            submission.student_submitter = student_submitter
            submission.guest_submitter = guest_submitter
            submission.save()
            messages.success(request, 'Your solution has been submitted successfully!')
            return redirect('quiz_detail', quiz_id=quiz_id)
    else:
        form = QuizSubmissionForm()
    
    return render(request, 'core/research/submit_quiz.html', {'form': form, 'quiz': quiz})


# ==================== ADMIN RESEARCH MANAGEMENT ====================

@login_required
def manage_research_teams(request):
    """Admin manages research teams"""
    teams = ResearchTeam.objects.all()
    return render(request, 'core/admin/manage_research_teams.html', {'teams': teams})


@login_required
def add_research_team(request):
    """Admin adds research team"""
    if request.method == 'POST':
        form = ResearchTeamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Research team added successfully!')
            return redirect('manage_research_teams')
    else:
        form = ResearchTeamForm()
    return render(request, 'core/admin/research_team_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_research_team(request, pk):
    """Admin edits research team"""
    team = get_object_or_404(ResearchTeam, pk=pk)
    if request.method == 'POST':
        form = ResearchTeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Research team updated successfully!')
            return redirect('manage_research_teams')
    else:
        form = ResearchTeamForm(instance=team)
    return render(request, 'core/admin/research_team_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_research_team(request, pk):
    """Admin deletes research team"""
    team = get_object_or_404(ResearchTeam, pk=pk)
    if request.method == 'POST':
        team.delete()
        messages.success(request, 'Research team deleted successfully!')
        return redirect('manage_research_teams')
    return render(request, 'core/admin/confirm_delete.html', {'object': team, 'type': 'Research Team'})


@login_required
def manage_research_articles(request):
    """Admin manages research articles"""
    articles = ResearchArticle.objects.all().select_related('team', 'created_by')
    return render(request, 'core/admin/manage_research_articles.html', {'articles': articles})


@login_required
def add_research_article(request):
    """Admin adds research article"""
    if request.method == 'POST':
        form = ResearchArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.created_by = request.user
            article.save()
            messages.success(request, 'Research article created successfully!')
            return redirect('manage_research_articles')
    else:
        form = ResearchArticleForm()
    return render(request, 'core/admin/research_article_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_research_article(request, pk):
    """Admin edits research article"""
    article = get_object_or_404(ResearchArticle, pk=pk)
    if request.method == 'POST':
        form = ResearchArticleForm(request.POST, instance=article)
        if form.is_valid():
            updated_article = form.save()
            
            # If status changed to Published, set publish date
            if updated_article.status == 'Published' and not updated_article.published_date:
                updated_article.published_date = timezone.now()
                updated_article.save()
            
            messages.success(request, 'Research article updated successfully!')
            return redirect('manage_research_articles')
    else:
        form = ResearchArticleForm(instance=article)
    return render(request, 'core/admin/research_article_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_research_article(request, pk):
    """Admin deletes research article"""
    article = get_object_or_404(ResearchArticle, pk=pk)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Research article deleted successfully!')
        return redirect('manage_research_articles')
    return render(request, 'core/admin/confirm_delete.html', {'object': article, 'type': 'Research Article'})


@login_required
def manage_contributions(request):
    """Admin manages all contributions"""
    contributions = ResearchContribution.objects.all().select_related(
        'article', 'student_contributor', 'guest_contributor', 'approved_by'
    ).order_by('-created_at')
    
    pending_count = contributions.filter(is_approved=False).count()
    approved_count = contributions.filter(is_approved=True).count()
    
    context = {
        'contributions': contributions,
        'pending_count': pending_count,
        'approved_count': approved_count,
    }
    return render(request, 'core/admin/manage_contributions.html', context)


@login_required
def approve_contribution(request, pk):
    """Admin approves a contribution"""
    contribution = get_object_or_404(ResearchContribution, pk=pk)
    
    if request.method == 'POST':
        section_order = request.POST.get('section_order', 0)
        contribution.is_approved = True
        contribution.approved_by = request.user
        contribution.approved_at = timezone.now()
        contribution.section_order = int(section_order)
        contribution.save()
        
        messages.success(request, f'Contribution by {contribution.get_contributor_name()} approved!')
        return redirect('manage_contributions')
    
    return render(request, 'core/admin/approve_contribution.html', {'contribution': contribution})


@login_required
def reject_contribution(request, pk):
    """Admin rejects a contribution"""
    contribution = get_object_or_404(ResearchContribution, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '')
        contribution.rejection_reason = reason
        contribution.delete()  # Or keep it with a rejected flag
        
        messages.success(request, 'Contribution rejected.')
        return redirect('manage_contributions')
    
    return render(request, 'core/admin/reject_contribution.html', {'contribution': contribution})


@login_required
def manage_guest_contributors(request):
    """Admin manages guest contributors"""
    guests = GuestContributor.objects.all().order_by('-created_at')
    pending_count = guests.filter(is_approved=False).count()
    approved_count = guests.filter(is_approved=True).count()
    
    context = {
        'guests': guests,
        'pending_count': pending_count,
        'approved_count': approved_count,
    }
    return render(request, 'core/admin/manage_guest_contributors.html', context)


@login_required
def approve_guest_contributor(request, pk):
    """Admin approves guest contributor"""
    guest = get_object_or_404(GuestContributor, pk=pk)
    guest.is_approved = True
    guest.approved_by = request.user
    guest.approved_at = timezone.now()
    guest.save()
    
    messages.success(request, f'Guest contributor {guest.full_name} approved!')
    return redirect('manage_guest_contributors')


@login_required
def reject_guest_contributor(request, pk):
    """Admin rejects guest contributor"""
    guest = get_object_or_404(GuestContributor, pk=pk)
    if request.method == 'POST':
        guest.delete()
        messages.success(request, 'Guest contributor application rejected.')
        return redirect('manage_guest_contributors')
    return render(request, 'core/admin/confirm_delete.html', {'object': guest, 'type': 'Guest Contributor'})


@login_required
def manage_research_quizzes(request):
    """Admin manages research quizzes"""
    quizzes = ResearchQuiz.objects.all().order_by('-created_at')
    return render(request, 'core/admin/manage_research_quizzes.html', {'quizzes': quizzes})


@login_required
def add_research_quiz(request):
    """Admin adds research quiz"""
    if request.method == 'POST':
        form = ResearchQuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Research quiz added successfully!')
            return redirect('manage_research_quizzes')
    else:
        form = ResearchQuizForm()
    return render(request, 'core/admin/research_quiz_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_research_quiz(request, pk):
    """Admin edits research quiz"""
    quiz = get_object_or_404(ResearchQuiz, pk=pk)
    if request.method == 'POST':
        form = ResearchQuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Research quiz updated successfully!')
            return redirect('manage_research_quizzes')
    else:
        form = ResearchQuizForm(instance=quiz)
    return render(request, 'core/admin/research_quiz_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_research_quiz(request, pk):
    """Admin deletes research quiz"""
    quiz = get_object_or_404(ResearchQuiz, pk=pk)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Research quiz deleted successfully!')
        return redirect('manage_research_quizzes')
    return render(request, 'core/admin/confirm_delete.html', {'object': quiz, 'type': 'Research Quiz'})


@login_required
def manage_quiz_submissions(request):
    """Admin manages quiz submissions"""
    submissions = QuizSubmission.objects.all().select_related(
        'quiz', 'student_submitter', 'guest_submitter', 'awarded_by'
    ).order_by('-created_at')
    
    pending_count = submissions.filter(is_awarded=False).count()
    awarded_count = submissions.filter(is_awarded=True).count()
    
    context = {
        'submissions': submissions,
        'pending_count': pending_count,
        'awarded_count': awarded_count,
    }
    return render(request, 'core/admin/manage_quiz_submissions.html', context)


@login_required
def award_quiz_submission(request, pk):
    """Admin awards a quiz submission"""
    submission = get_object_or_404(QuizSubmission, pk=pk)
    
    if request.method == 'POST':
        comment = request.POST.get('award_comment', '')
        submission.is_awarded = True
        submission.award_comment = comment
        submission.awarded_by = request.user
        submission.awarded_at = timezone.now()
        submission.save()
        
        messages.success(request, f'Quiz submission by {submission.get_submitter_name()} awarded!')
        return redirect('manage_quiz_submissions')
    
    return render(request, 'core/admin/award_quiz_submission.html', {'submission': submission})


@login_required
def view_quiz_submission_detail(request, pk):
    """Admin views detailed quiz submission"""
    submission = get_object_or_404(QuizSubmission, pk=pk)
    return render(request, 'core/admin/quiz_submission_detail.html', {'submission': submission})