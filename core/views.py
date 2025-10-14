from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from .models import( Staff, Exco, PastQuestion, 
                    LibraryResource, Testimonial, Announcement, 
                    Student, Semester, Course, CGPACalculation, DepartmentalDues, 
                    CourseHandbook, Timetable, AcademicCalendar)
from .forms import (StaffForm, ExcoForm, PastQuestionForm, LibraryResourceForm, TestimonialForm, 
                    AnnouncementForm, StudentRegistrationForm, StudentLoginForm, 
                    StudentProfileForm, SemesterForm, CourseForm,  DepartmentalDuesForm,
                    CourseHandbookForm, TimetableForm, AcademicCalendarForm)
import json
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string

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