from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from .models import *
from .forms import *
import json
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging
from core.paystack import initialize_student_payment, verify_student_payment
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import hashlib
import hmac
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_control
import os
from django.conf import settings
from functools import wraps

logger = logging.getLogger(__name__)


# Add this to your views.py

def verify_receipt(request):
    """
    Public receipt verification page
    Verifies departmental dues receipts using watermark code
    """
    verification_result = None
    error_message = None
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code', '').strip()
        
        print(f"\n{'='*60}")
        print(f"VERIFICATION ATTEMPT")
        print(f"{'='*60}")
        print(f"Verification Code: '{verification_code}'")
        print(f"Code Length: {len(verification_code)}")
        print(f"POST Method: {request.method}")
        print(f"User IP: {get_client_ip(request)}")
        
        # Validate input
        if not verification_code:
            error_message = 'Please enter a verification code.'
            verification_result = {
                'is_valid': False,
                'message': error_message
            }
            print(f"❌ Empty verification code")
        
        elif len(verification_code) < 5:
            error_message = 'Verification code is too short. Check you copied it correctly.'
            verification_result = {
                'is_valid': False,
                'message': error_message
            }
            print(f"❌ Code too short: {len(verification_code)} chars")
        
        else:
            try:
                # Search for matching watermark code
                print(f"\n🔍 Searching database for watermark_code='{verification_code}'")
                
                dues = DepartmentalDues.objects.get(
                    watermark_code=verification_code,
                    is_approved=True
                )
                
                print(f"✓ FOUND!")
                print(f"  Receipt Number: {dues.receipt_number}")
                print(f"  Student: {dues.student.full_name}")
                print(f"  Amount: ₦{dues.amount_paid}")
                print(f"  Session: {dues.academic_session}")
                
                # Log successful verification
                ReceiptVerification.objects.create(
                    receipt=dues,
                    verification_code=verification_code,
                    is_valid=True,
                    ip_address=get_client_ip(request)
                )
                
                # Build result dictionary
                verification_result = {
                    'is_valid': True,
                    'dues': dues,
                    'student': dues.student,
                    'verified_at': timezone.now(),
                    'message': 'Receipt verified successfully!'
                }
                
                logger.info(
                    f"✓ Receipt {dues.receipt_number} verified by {get_client_ip(request)}"
                )
                
                print(f"\n✓✓✓ VERIFICATION SUCCESSFUL ✓✓✓\n")
            
            except DepartmentalDues.DoesNotExist:
                print(f"❌ NOT FOUND!")
                print(f"  Checked for: watermark_code='{verification_code}' AND is_approved=True")
                
                # Debug: Check what codes exist
                similar = DepartmentalDues.objects.filter(
                    watermark_code__icontains=verification_code[:10]
                ) if len(verification_code) >= 10 else None
                
                if similar and similar.exists():
                    print(f"  Similar codes found: {similar.count()}")
                    for item in similar[:3]:
                        print(f"    - {item.watermark_code} (Approved: {item.is_approved})")
                else:
                    print(f"  No similar codes in database")
                
                # Log failed verification
                ReceiptVerification.objects.create(
                    verification_code=verification_code,
                    is_valid=False,
                    ip_address=get_client_ip(request)
                )
                
                error_message = (
                    'Invalid verification code. This receipt either does not exist, '
                    'has not been approved yet, or the code is incorrect.'
                )
                
                verification_result = {
                    'is_valid': False,
                    'message': error_message
                }
                
                logger.warning(
                    f"❌ Failed verification attempt for {verification_code} "
                    f"from {get_client_ip(request)}"
                )
                
                print(f"\n❌ VERIFICATION FAILED ❌\n")
        
        print(f"Result: {verification_result}")
        print(f"{'='*60}\n")
    
    context = {
        'verification_result': verification_result,
        'error_message': error_message
    }
    
    return render(request, 'core/verify_receipt.html', context)

def financial_access_required(view_func):
    """Decorator to restrict access to financial features - based on username only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Only allow specific usernames
        if request.user.username in ['ibeawuchi', 'finsec']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'You do not have permission to access this feature.')
        return redirect('admin_dashboard')
    
    return wrapper


@require_GET
@cache_control(max_age=0, no_cache=True, must_revalidate=True, no_store=True)
def service_worker(request):
    """Serve the service worker file from root"""
    try:
        # Try to read from static files
        sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'service-worker.js')
        
        # If not in static, try root
        if not os.path.exists(sw_path):
            sw_path = os.path.join(settings.BASE_DIR, 'service-worker.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            sw_content = f.read()
        
        return HttpResponse(
            sw_content,
            content_type='application/javascript; charset=utf-8',
            headers={
                'Service-Worker-Allowed': '/',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            }
        )
    except FileNotFoundError:
        # Return a basic service worker if file not found
        basic_sw = '''
        const CACHE_NAME = 'futo-bme-basic';
        
        self.addEventListener('install', (event) => {
            console.log('[SW] Installing...');
            self.skipWaiting();
        });
        
        self.addEventListener('activate', (event) => {
            console.log('[SW] Activating...');
            event.waitUntil(self.clients.claim());
        });
        
        self.addEventListener('fetch', (event) => {
            // Let network handle all requests
        });
        '''
        return HttpResponse(
            basic_sw,
            content_type='application/javascript; charset=utf-8'
        )

@require_GET
@cache_control(max_age=0, no_cache=True, must_revalidate=True, no_store=True)
def manifest_json(request):
    """Serve the manifest.json file"""
    import json
    
    manifest = {
        "name": "FUTO BME Portal",
        "short_name": "FUTO BME",
        "description": "Federal University of Technology Owerri - Biomedical Engineering Department Portal",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#8B1538",
        "theme_color": "#8B1538",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg",
                "sizes": "192x192",
                "type": "image/jpeg",
                "purpose": "any maskable"
            },
            {
                "src": "https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg",
                "sizes": "512x512",
                "type": "image/jpeg",
                "purpose": "any maskable"
            }
        ],
        "shortcuts": [
            {
                "name": "Student Portal",
                "url": "/student/login/",
                "icons": [{
                    "src": "https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg",
                    "sizes": "96x96"
                }]
            },
            {
                "name": "Past Questions",
                "url": "/past-questions/",
                "icons": [{
                    "src": "https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg",
                    "sizes": "96x96"
                }]
            }
        ]
    }
    
    return HttpResponse(
        json.dumps(manifest, indent=2),
        content_type='application/manifest+json'
    )



@csrf_exempt
def paystack_webhook(request):
    if request.method == 'POST':
        # Verify signature
        signature = request.headers.get('X-Paystack-Signature')
        body = request.body
        
        hash_value = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        
        if hash_value == signature:
            import json
            data = json.loads(body)
            
            if data['event'] == 'charge.success':
                reference = data['data']['reference']
                verify_student_payment(reference)
                
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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
    recent_staff = Staff.objects.all()[:12]
    current_excos = Exco.objects.all()[:12]
    recent_resources = LibraryResource.objects.all()[:12]
    recent_questions = PastQuestion.objects.all()[:12]
    
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
# @login_required
# def admin_dashboard(request):
#     """Comprehensive admin dashboard with all statistics"""
#     from django.db.models import Sum, Avg, Count, Q
#     from datetime import timedelta
    
#     # ==================== CONTENT MANAGEMENT STATS ====================
#     content_stats = {
#         'staff_count': Staff.objects.count(),
#         'excos_count': Exco.objects.count(),
#         'past_questions_count': PastQuestion.objects.count(),
#         'library_count': LibraryResource.objects.count(),
#         'testimonials_total': Testimonial.objects.count(),
#         'testimonials_pending': Testimonial.objects.filter(is_approved=False).count(),
#         'testimonials_approved': Testimonial.objects.filter(is_approved=True).count(),
#         'announcements_total': Announcement.objects.count(),
#         'announcements_active': Announcement.objects.filter(is_active=True).count(),
#     }
    
#     # ==================== STUDENT PORTAL STATS ====================
#     student_stats = {
#         'total_registered': Student.objects.count(),
#         'paid_students': Student.objects.filter(has_paid=True).count(),
#         'pending_payments': Student.objects.filter(has_paid=False).count(),
#         'registered_numbers': RegisteredRegNumber.objects.filter(is_active=True).count(),
#         'registration_requests_pending': RegistrationRequest.objects.filter(status='pending').count(),
#         'registration_requests_total': RegistrationRequest.objects.count(),
#     }
    
#     # Payment Statistics
#     payment_stats = {
#         'total_payments': StudentPayment.objects.count(),
#         'successful_payments': StudentPayment.objects.filter(status='success').count(),
#         'pending_payments': StudentPayment.objects.filter(status='pending').count(),
#         'failed_payments': StudentPayment.objects.filter(status='failed').count(),
#         'total_revenue': StudentPayment.objects.filter(
#             status='success'
#         ).aggregate(Sum('department_amount'))['department_amount__sum'] or 0,
#         'total_charges': StudentPayment.objects.filter(
#             status='success'
#         ).aggregate(Sum('charges'))['charges__sum'] or 0,
#     }
    
#     # ==================== ACADEMIC RESOURCES STATS ====================
#     academic_stats = {
#         'course_handbook_total': CourseHandbook.objects.count(),
#         'course_handbook_by_level': CourseHandbook.objects.values('level').annotate(
#             count=Count('id')
#         ).order_by('level'),
#         'timetables_total': Timetable.objects.count(),
#         'timetables_active': Timetable.objects.filter(is_active=True).count(),
#         'exam_timetables': Timetable.objects.filter(timetable_type='Exam').count(),
#         'class_timetables': Timetable.objects.filter(timetable_type='Class').count(),
#         'calendars_total': AcademicCalendar.objects.count(),
#         'calendars_active': AcademicCalendar.objects.filter(is_active=True).count(),
#     }
    
#     # ==================== DEPARTMENTAL DUES STATS ====================
#     dues_stats = {
#         'total_dues': DepartmentalDues.objects.count(),
#         'approved_dues': DepartmentalDues.objects.filter(is_approved=True).count(),
#         'pending_dues': DepartmentalDues.objects.filter(is_approved=False).count(),
#         'dues_revenue': DepartmentalDues.objects.filter(
#             is_approved=True
#         ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
#         'recent_prints': ReceiptPrintLog.objects.count(),
#         'verification_attempts': ReceiptVerification.objects.count(),
#         'valid_verifications': ReceiptVerification.objects.filter(is_valid=True).count(),
#     }
    
#     # ==================== RESEARCH CLUB STATS ====================
#     research_stats = {
#         # Teams
#         'teams_total': ResearchTeam.objects.count(),
#         'teams_active': ResearchTeam.objects.filter(is_active=True).count(),
#         'total_team_members': TeamMembership.objects.count(),
        
#         # Articles
#         'articles_total': ResearchArticle.objects.count(),
#         'articles_draft': ResearchArticle.objects.filter(status='Draft').count(),
#         'articles_in_progress': ResearchArticle.objects.filter(status='In Progress').count(),
#         'articles_under_review': ResearchArticle.objects.filter(status='Under Review').count(),
#         'articles_published': ResearchArticle.objects.filter(status='Published').count(),
#         'total_article_views': ResearchArticle.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0,
#         'total_article_likes': ResearchArticle.objects.aggregate(Sum('likes_count'))['likes_count__sum'] or 0,
        
#         # Contributions
#         'contributions_total': ResearchContribution.objects.count(),
#         'contributions_pending': ResearchContribution.objects.filter(is_approved=False).count(),
#         'contributions_approved': ResearchContribution.objects.filter(is_approved=True).count(),
#         'student_contributions': ResearchContribution.objects.filter(
#             student_contributor__isnull=False
#         ).count(),
#         'guest_contributions': ResearchContribution.objects.filter(
#             guest_contributor__isnull=False
#         ).count(),
        
#         # Registrations
#         'club_registrations_total': ResearchClubRegistration.objects.count(),
#         'club_registrations_pending': ResearchClubRegistration.objects.filter(
#             payment_status='pending'
#         ).count(),
#         'club_registrations_verified': ResearchClubRegistration.objects.filter(
#             payment_status='verified'
#         ).count(),
#         'club_registrations_approved': ResearchClubRegistration.objects.filter(
#             is_approved=True
#         ).count(),
#         'club_revenue': ResearchClubRegistration.objects.filter(
#             payment_status='verified'
#         ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        
#         # Guest Contributors
#         'guests_total': GuestContributor.objects.count(),
#         'guests_pending': GuestContributor.objects.filter(payment_status='pending').count(),
#         'guests_verified': GuestContributor.objects.filter(payment_status='verified').count(),
#         'guests_approved': GuestContributor.objects.filter(is_approved=True).count(),
#         'guest_revenue': GuestContributor.objects.filter(
#             payment_status='verified'
#         ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        
#         # Quizzes
#         'quizzes_total': ResearchQuiz.objects.count(),
#         'quizzes_active': ResearchQuiz.objects.filter(is_active=True).count(),
#         'quiz_submissions_total': QuizSubmission.objects.count(),
#         'quiz_submissions_pending': QuizSubmission.objects.filter(is_awarded=False).count(),
#         'quiz_submissions_awarded': QuizSubmission.objects.filter(is_awarded=True).count(),
#     }
    
#     # ==================== FINANCIAL SUMMARY ====================
#     financial_summary = {
#         'portal_fees': payment_stats['total_revenue'],
#         'departmental_dues': dues_stats['dues_revenue'],
#         'research_club': research_stats['club_revenue'],
#         'guest_contributors': research_stats['guest_revenue'],
#         'platform_charges': payment_stats['total_charges'],
#     }
#     financial_summary['total_revenue'] = sum([
#         financial_summary['portal_fees'],
#         financial_summary['departmental_dues'],
#         financial_summary['research_club'],
#         financial_summary['guest_contributors'],
#     ])
#     financial_summary['net_revenue'] = (
#         financial_summary['total_revenue'] - financial_summary['platform_charges']
#     )
    
#     # ==================== RECENT ACTIVITIES ====================
#     # Get recent items (last 7 days for some, all-time top 5 for others)
#     seven_days_ago = timezone.now() - timedelta(days=7)
    
#     recent_activities = {
#         'students': Student.objects.order_by('-created_at')[:5],
#         'payments': StudentPayment.objects.filter(
#             status='success'
#         ).order_by('-created_at')[:5],
#         'registration_requests': RegistrationRequest.objects.filter(
#             status='pending'
#         ).order_by('-created_at')[:5],
#         'dues_pending': DepartmentalDues.objects.filter(
#             is_approved=False
#         ).order_by('-created_at')[:5],
#         'testimonials_pending': Testimonial.objects.filter(
#             is_approved=False
#         ).order_by('-created_at')[:5],
#         'club_registrations_pending': ResearchClubRegistration.objects.filter(
#             payment_status='pending'
#         ).order_by('-registered_at')[:5],
#         'guests_pending': GuestContributor.objects.filter(
#             payment_status='pending'
#         ).order_by('-created_at')[:5],
#         'contributions_pending': ResearchContribution.objects.filter(
#             is_approved=False
#         ).select_related('article', 'student_contributor', 'guest_contributor').order_by('-created_at')[:5],
#         'quiz_submissions_pending': QuizSubmission.objects.filter(
#             is_awarded=False
#         ).select_related('quiz', 'student_submitter', 'guest_submitter').order_by('-created_at')[:5],
#     }
    
#     # ==================== CHARTS DATA ====================
#     # Student registration trend (last 30 days)
#     from django.db.models.functions import TruncDate
#     thirty_days_ago = timezone.now() - timedelta(days=30)
    
#     registration_trend = Student.objects.filter(
#         created_at__gte=thirty_days_ago
#     ).annotate(
#         date=TruncDate('created_at')
#     ).values('date').annotate(
#         count=Count('reg_number')
#     ).order_by('date')
    
#     # Payment status distribution
#     payment_distribution = {
#         'success': StudentPayment.objects.filter(status='success').count(),
#         'pending': StudentPayment.objects.filter(status='pending').count(),
#         'failed': StudentPayment.objects.filter(status='failed').count(),
#     }
    
#     # Research articles by status
#     article_distribution = {
#         'draft': research_stats['articles_draft'],
#         'in_progress': research_stats['articles_in_progress'],
#         'under_review': research_stats['articles_under_review'],
#         'published': research_stats['articles_published'],
#     }
    
#     # Top contributors
#     top_contributors = ResearchContribution.objects.filter(
#         is_approved=True,
#         student_contributor__isnull=False
#     ).values(
#         'student_contributor__full_name',
#         'student_contributor__reg_number'
#     ).annotate(
#         contribution_count=Count('id')
#     ).order_by('-contribution_count')[:5]
    
#     # ==================== ALERTS & WARNINGS ====================
#     alerts = []
    
#     # Check for pending items
#     if recent_activities['registration_requests'].count() > 0:
#         alerts.append({
#             'type': 'warning',
#             'message': f"{recent_activities['registration_requests'].count()} registration requests pending approval",
#             'url': 'manage_registration_requests'
#         })
    
#     if recent_activities['dues_pending'].count() > 0:
#         alerts.append({
#             'type': 'info',
#             'message': f"{recent_activities['dues_pending'].count()} departmental dues pending approval",
#             'url': 'manage_departmental_dues'
#         })
    
#     if recent_activities['testimonials_pending'].count() > 0:
#         alerts.append({
#             'type': 'info',
#             'message': f"{recent_activities['testimonials_pending'].count()} testimonials pending review",
#             'url': 'manage_testimonials'
#         })
    
#     if research_stats['contributions_pending'] > 0:
#         alerts.append({
#             'type': 'warning',
#             'message': f"{research_stats['contributions_pending']} research contributions pending approval",
#             'url': 'manage_contributions'
#         })
    
#     if research_stats['club_registrations_pending'] > 0:
#         alerts.append({
#             'type': 'warning',
#             'message': f"{research_stats['club_registrations_pending']} research club registrations pending verification",
#             'url': 'manage_research_registrations'
#         })
    
#     if research_stats['guests_pending'] > 0:
#         alerts.append({
#             'type': 'info',
#             'message': f"{research_stats['guests_pending']} guest contributor applications pending",
#             'url': 'manage_guest_contributors'
#         })
    
#     if research_stats['quiz_submissions_pending'] > 0:
#         alerts.append({
#             'type': 'info',
#             'message': f"{research_stats['quiz_submissions_pending']} quiz submissions pending review",
#             'url': 'manage_quiz_submissions'
#         })
    
#     # Compile all data
#     context = {
#         'content_stats': content_stats,
#         'student_stats': student_stats,
#         'payment_stats': payment_stats,
#         'academic_stats': academic_stats,
#         'dues_stats': dues_stats,
#         'research_stats': research_stats,
#         'financial_summary': financial_summary,
#         'recent_activities': recent_activities,
#         'registration_trend': list(registration_trend),
#         'payment_distribution': payment_distribution,
#         'article_distribution': article_distribution,
#         'top_contributors': list(top_contributors),
#         'alerts': alerts,
#     }
    
#     return render(request, 'core/admin/dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Comprehensive admin dashboard with all statistics"""
    from django.db.models import Sum, Avg, Count, Q
    from datetime import timedelta
    
    # Check if user has financial access - based on username only
    has_financial_access = request.user.username in ['ibeawuchi', 'finsec']
    
    # ==================== CONTENT MANAGEMENT STATS ====================
    content_stats = {
        'staff_count': Staff.objects.count(),
        'excos_count': Exco.objects.count(),
        'past_questions_count': PastQuestion.objects.count(),
        'library_count': LibraryResource.objects.count(),
        'testimonials_total': Testimonial.objects.count(),
        'testimonials_pending': Testimonial.objects.filter(is_approved=False).count(),
        'testimonials_approved': Testimonial.objects.filter(is_approved=True).count(),
        'announcements_total': Announcement.objects.count(),
        'announcements_active': Announcement.objects.filter(is_active=True).count(),
    }
    
    # ==================== STUDENT PORTAL STATS ====================
    student_stats = {
        'total_registered': Student.objects.count(),
        'paid_students': Student.objects.filter(has_paid=True).count(),
        'pending_payments': Student.objects.filter(has_paid=False).count(),
        'registered_numbers': RegisteredRegNumber.objects.filter(is_active=True).count(),
        'registration_requests_pending': RegistrationRequest.objects.filter(status='pending').count(),
        'registration_requests_total': RegistrationRequest.objects.count(),
    }
    
    # Payment Statistics
    payment_stats = {
        'total_payments': StudentPayment.objects.count(),
        'successful_payments': StudentPayment.objects.filter(status='success').count(),
        'pending_payments': StudentPayment.objects.filter(status='pending').count(),
        'failed_payments': StudentPayment.objects.filter(status='failed').count(),
        'total_revenue': StudentPayment.objects.filter(
            status='success'
        ).aggregate(Sum('department_amount'))['department_amount__sum'] or 0,
        'total_charges': StudentPayment.objects.filter(
            status='success'
        ).aggregate(Sum('charges'))['charges__sum'] or 0,
    }
    
    # ==================== ACADEMIC RESOURCES STATS ====================
    academic_stats = {
        'course_handbook_total': CourseHandbook.objects.count(),
        'course_handbook_by_level': CourseHandbook.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level'),
        'timetables_total': Timetable.objects.count(),
        'timetables_active': Timetable.objects.filter(is_active=True).count(),
        'exam_timetables': Timetable.objects.filter(timetable_type='Exam').count(),
        'class_timetables': Timetable.objects.filter(timetable_type='Class').count(),
        'calendars_total': AcademicCalendar.objects.count(),
        'calendars_active': AcademicCalendar.objects.filter(is_active=True).count(),
    }
    
    # ==================== DEPARTMENTAL DUES STATS (Only for ibeawuchi and finsec) ====================
    dues_stats = None
    if has_financial_access:
        dues_stats = {
            'total_dues': DepartmentalDues.objects.count(),
            'approved_dues': DepartmentalDues.objects.filter(is_approved=True).count(),
            'pending_dues': DepartmentalDues.objects.filter(is_approved=False).count(),
            'dues_revenue': DepartmentalDues.objects.filter(
                is_approved=True
            ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
            'recent_prints': ReceiptPrintLog.objects.count(),
            'verification_attempts': ReceiptVerification.objects.count(),
            'valid_verifications': ReceiptVerification.objects.filter(is_valid=True).count(),
        }
    
    # ==================== RESEARCH CLUB STATS ====================
    research_stats = {
        # Teams
        'teams_total': ResearchTeam.objects.count(),
        'teams_active': ResearchTeam.objects.filter(is_active=True).count(),
        'total_team_members': TeamMembership.objects.count(),
        
        # Articles
        'articles_total': ResearchArticle.objects.count(),
        'articles_draft': ResearchArticle.objects.filter(status='Draft').count(),
        'articles_in_progress': ResearchArticle.objects.filter(status='In Progress').count(),
        'articles_under_review': ResearchArticle.objects.filter(status='Under Review').count(),
        'articles_published': ResearchArticle.objects.filter(status='Published').count(),
        'total_article_views': ResearchArticle.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0,
        'total_article_likes': ResearchArticle.objects.aggregate(Sum('likes_count'))['likes_count__sum'] or 0,
        
        # Contributions
        'contributions_total': ResearchContribution.objects.count(),
        'contributions_pending': ResearchContribution.objects.filter(is_approved=False).count(),
        'contributions_approved': ResearchContribution.objects.filter(is_approved=True).count(),
        'student_contributions': ResearchContribution.objects.filter(
            student_contributor__isnull=False
        ).count(),
        'guest_contributions': ResearchContribution.objects.filter(
            guest_contributor__isnull=False
        ).count(),
        
        # Registrations
        'club_registrations_total': ResearchClubRegistration.objects.count(),
        'club_registrations_pending': ResearchClubRegistration.objects.filter(
            payment_status='pending'
        ).count(),
        'club_registrations_verified': ResearchClubRegistration.objects.filter(
            payment_status='verified'
        ).count(),
        'club_registrations_approved': ResearchClubRegistration.objects.filter(
            is_approved=True
        ).count(),
        'club_revenue': ResearchClubRegistration.objects.filter(
            payment_status='verified'
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        
        # Guest Contributors
        'guests_total': GuestContributor.objects.count(),
        'guests_pending': GuestContributor.objects.filter(payment_status='pending').count(),
        'guests_verified': GuestContributor.objects.filter(payment_status='verified').count(),
        'guests_approved': GuestContributor.objects.filter(is_approved=True).count(),
        'guest_revenue': GuestContributor.objects.filter(
            payment_status='verified'
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        
        # Quizzes
        'quizzes_total': ResearchQuiz.objects.count(),
        'quizzes_active': ResearchQuiz.objects.filter(is_active=True).count(),
        'quiz_submissions_total': QuizSubmission.objects.count(),
        'quiz_submissions_pending': QuizSubmission.objects.filter(is_awarded=False).count(),
        'quiz_submissions_awarded': QuizSubmission.objects.filter(is_awarded=True).count(),
    }
    
    # ==================== FINANCIAL SUMMARY (Only for ibeawuchi and finsec) ====================
    financial_summary = None
    if has_financial_access:
        financial_summary = {
            'portal_fees': payment_stats['total_revenue'],
            'departmental_dues': dues_stats['dues_revenue'],
            'research_club': research_stats['club_revenue'],
            'guest_contributors': research_stats['guest_revenue'],
            'platform_charges': payment_stats['total_charges'],
        }
        financial_summary['total_revenue'] = sum([
            financial_summary['portal_fees'],
            financial_summary['departmental_dues'],
            financial_summary['research_club'],
            financial_summary['guest_contributors'],
        ])
        financial_summary['net_revenue'] = (
            financial_summary['total_revenue'] - financial_summary['platform_charges']
        )
    
    # ==================== RECENT ACTIVITIES ====================
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    recent_activities = {
        'students': Student.objects.order_by('-created_at')[:5],
        'payments': StudentPayment.objects.filter(
            status='success'
        ).order_by('-created_at')[:5],
        'registration_requests': RegistrationRequest.objects.filter(
            status='pending'
        ).order_by('-created_at')[:5],
        'testimonials_pending': Testimonial.objects.filter(
            is_approved=False
        ).order_by('-created_at')[:5],
        'club_registrations_pending': ResearchClubRegistration.objects.filter(
            payment_status='pending'
        ).order_by('-registered_at')[:5],
        'guests_pending': GuestContributor.objects.filter(
            payment_status='pending'
        ).order_by('-created_at')[:5],
        'contributions_pending': ResearchContribution.objects.filter(
            is_approved=False
        ).select_related('article', 'student_contributor', 'guest_contributor').order_by('-created_at')[:5],
        'quiz_submissions_pending': QuizSubmission.objects.filter(
            is_awarded=False
        ).select_related('quiz', 'student_submitter', 'guest_submitter').order_by('-created_at')[:5],
    }
    
    # Add dues activities only for financial users
    if has_financial_access:
        recent_activities['dues_pending'] = DepartmentalDues.objects.filter(
            is_approved=False
        ).order_by('-created_at')[:5]
    
    # ==================== CHARTS DATA ====================
    from django.db.models.functions import TruncDate
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    registration_trend = Student.objects.filter(
        created_at__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('reg_number')
    ).order_by('date')
    
    payment_distribution = {
        'success': StudentPayment.objects.filter(status='success').count(),
        'pending': StudentPayment.objects.filter(status='pending').count(),
        'failed': StudentPayment.objects.filter(status='failed').count(),
    }
    
    article_distribution = {
        'draft': research_stats['articles_draft'],
        'in_progress': research_stats['articles_in_progress'],
        'under_review': research_stats['articles_under_review'],
        'published': research_stats['articles_published'],
    }
    
    top_contributors = ResearchContribution.objects.filter(
        is_approved=True,
        student_contributor__isnull=False
    ).values(
        'student_contributor__full_name',
        'student_contributor__reg_number'
    ).annotate(
        contribution_count=Count('id')
    ).order_by('-contribution_count')[:5]
    
    # ==================== ALERTS & WARNINGS ====================
    alerts = []
    
    if recent_activities['registration_requests'].count() > 0:
        alerts.append({
            'type': 'warning',
            'message': f"{recent_activities['registration_requests'].count()} registration requests pending approval",
            'url': 'manage_registration_requests'
        })
    
    # Only show dues alert for financial users
    if has_financial_access and recent_activities.get('dues_pending') and recent_activities['dues_pending'].count() > 0:
        alerts.append({
            'type': 'info',
            'message': f"{recent_activities['dues_pending'].count()} departmental dues pending approval",
            'url': 'manage_departmental_dues'
        })
    
    if recent_activities['testimonials_pending'].count() > 0:
        alerts.append({
            'type': 'info',
            'message': f"{recent_activities['testimonials_pending'].count()} testimonials pending review",
            'url': 'manage_testimonials'
        })
    
    if research_stats['contributions_pending'] > 0:
        alerts.append({
            'type': 'warning',
            'message': f"{research_stats['contributions_pending']} research contributions pending approval",
            'url': 'manage_contributions'
        })
    
    if research_stats['club_registrations_pending'] > 0:
        alerts.append({
            'type': 'warning',
            'message': f"{research_stats['club_registrations_pending']} research club registrations pending verification",
            'url': 'manage_research_registrations'
        })
    
    if research_stats['guests_pending'] > 0:
        alerts.append({
            'type': 'info',
            'message': f"{research_stats['guests_pending']} guest contributor applications pending",
            'url': 'manage_guest_contributors'
        })
    
    if research_stats['quiz_submissions_pending'] > 0:
        alerts.append({
            'type': 'info',
            'message': f"{research_stats['quiz_submissions_pending']} quiz submissions pending review",
            'url': 'manage_quiz_submissions'
        })
    
    # Compile context
    context = {
        'content_stats': content_stats,
        'student_stats': student_stats,
        'payment_stats': payment_stats,
        'academic_stats': academic_stats,
        'dues_stats': dues_stats,
        'research_stats': research_stats,
        'financial_summary': financial_summary,
        'recent_activities': recent_activities,
        'registration_trend': list(registration_trend),
        'payment_distribution': payment_distribution,
        'article_distribution': article_distribution,
        'top_contributors': list(top_contributors),
        'alerts': alerts,
        'has_financial_access': has_financial_access,
    }
    
    return render(request, 'core/admin/dashboard.html', context)

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
    """Updated registration view with payment"""
    if request.session.get('student_reg_number'):
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            student = form.save()
            
            # Store student reg number in session temporarily
            request.session['pending_payment_student'] = student.reg_number
            
            messages.success(
                request, 
                f'Account created successfully! Please complete payment to access your dashboard.'
            )
            return redirect('student_payment')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'core/student/register.html', {'form': form})

def student_payment(request):
    """Payment page for new students"""
    reg_number = request.session.get('pending_payment_student')
    
    if not reg_number:
        messages.error(request, 'Please register first.')
        return redirect('student_register')
    
    try:
        student = Student.objects.get(reg_number=reg_number)
    except Student.DoesNotExist:
        messages.error(request, 'Student account not found.')
        return redirect('student_register')
    
    # Check if already paid
    if student.has_paid:
        request.session['student_reg_number'] = student.reg_number
        if 'pending_payment_student' in request.session:
            del request.session['pending_payment_student']
        return redirect('student_dashboard')
    
    # Check for existing payment
    try:
        payment = StudentPayment.objects.get(student=student)
        if payment.status == 'success' and payment.is_verified:
            student.has_paid = True
            student.save()
            request.session['student_reg_number'] = student.reg_number
            if 'pending_payment_student' in request.session:
                del request.session['pending_payment_student']
            return redirect('student_dashboard')
    except StudentPayment.DoesNotExist:
        payment = None
    
    # Initialize payment on POST
    if request.method == 'POST':
        result = initialize_student_payment(student, request)
        
        if result.get('status'):
            # Redirect to Paystack payment page
            return redirect(result['authorization_url'])
        else:
            messages.error(request, result.get('message', 'Payment initialization failed'))
    
    context = {
        'student': student,
        'amount': 1250,
        'department_amount': 1000,
        'charges': 250,
        'payment': payment,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY
    }
    
    return render(request, 'core/student/payment.html', context)


def verify_payment(request):
    """Verify payment callback from Paystack"""
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'No payment reference provided')
        return redirect('student_login')
    
    # DEBUG: Log what we're looking for
    print(f"DEBUG: Looking for payment with reference: {reference}")
    
    # Try to find payment by either our reference OR Paystack's reference
    from core.models import StudentPayment
    
    try:
        # First try to find by our reference
        payment = StudentPayment.objects.get(reference=reference)
        print(f"DEBUG: Found payment by our reference")
    except StudentPayment.DoesNotExist:
        try:
            # If not found, try by Paystack reference
            payment = StudentPayment.objects.get(paystack_reference=reference)
            print(f"DEBUG: Found payment by Paystack reference")
        except StudentPayment.DoesNotExist:
            # If still not found, check if student has a pending payment
            if request.session.get('pending_payment_student'):
                reg_number = request.session.get('pending_payment_student')
                try:
                    from core.models import Student
                    student = Student.objects.get(reg_number=reg_number)
                    payment = StudentPayment.objects.filter(student=student).first()
                    
                    if payment:
                        print(f"DEBUG: Found payment by student lookup")
                        # Update the reference to match what Paystack returned
                        payment.paystack_reference = reference
                        payment.save()
                    else:
                        raise StudentPayment.DoesNotExist
                except:
                    messages.error(request, 'Payment record not found. Please contact support.')
                    return redirect('student_payment')
            else:
                messages.error(request, 'Payment record not found. Please contact support.')
                return redirect('student_login')
    
    # Verify payment with Paystack
    from core.paystack import verify_student_payment
    result = verify_student_payment(reference)
    
    if result.get('status'):
        student = result['student']
        
        # Log the student in
        request.session['student_reg_number'] = student.reg_number
        
        # Clear pending payment session
        if 'pending_payment_student' in request.session:
            del request.session['pending_payment_student']
        
        messages.success(
            request, 
            f'Payment successful! Welcome to FUTO BME Portal, {student.full_name}!'
        )
        return redirect('student_dashboard')
    else:
        messages.error(request, result.get('message', 'Payment verification failed'))
        return redirect('student_payment') 

def student_login(request):
    """Updated login view to check payment status"""
    if request.session.get('student_reg_number'):
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            reg_number = form.cleaned_data['reg_number']
            password = form.cleaned_data['password']
            
            try:
                student = Student.objects.get(reg_number=reg_number)
                
                # Check if password matches
                if student.check_password(password):
                    # Check if student has paid
                    if not student.has_paid:
                        request.session['pending_payment_student'] = student.reg_number
                        messages.warning(request, 'Please complete payment to access your dashboard.')
                        return redirect('student_payment')
                    
                    request.session['student_reg_number'] = student.reg_number
                    messages.success(request, f'Welcome back, {student.full_name}!')
                    return redirect('student_dashboard')
                else:
                    messages.error(request, 'Invalid password. Please try again.')
            except Student.DoesNotExist:
                messages.error(request, 'Invalid registration number or password.')
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
        
        # Verify payment status
        reg_number = request.session.get('student_reg_number')
        try:
            student = Student.objects.get(reg_number=reg_number)
            if not student.has_paid:
                request.session['pending_payment_student'] = student.reg_number
                del request.session['student_reg_number']
                messages.warning(request, 'Please complete payment to access your dashboard.')
                return redirect('student_payment')
        except Student.DoesNotExist:
            del request.session['student_reg_number']
            messages.error(request, 'Student account not found.')
            return redirect('student_login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def registration_request(request):
    """Allow students not in system to request registration"""
    if request.method == 'POST':
        form = RegistrationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save()
            messages.success(
                request,
                'Your registration request has been submitted successfully! '
                'Admin will review your request and contact you via email.'
            )
            return redirect('index')
    else:
        form = RegistrationRequestForm()
    
    return render(request, 'core/student/registration_request.html', {'form': form})


@login_required
def manage_registered_numbers(request):
    """Admin view to manage registered registration numbers"""
    numbers = RegisteredRegNumber.objects.all().order_by('-date_registered')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        numbers = numbers.filter(
            Q(reg_number__icontains=search) | 
            Q(full_name__icontains=search)
        )
    
    # Level filter
    level = request.GET.get('level', '')
    if level:
        numbers = numbers.filter(level=level)
    
    context = {
        'numbers': numbers,
        'total_count': numbers.count(),
        'active_count': numbers.filter(is_active=True).count(),
        'search': search,
        'selected_level': level,
    }
    return render(request, 'core/admin/manage_registered_numbers.html', context)


@login_required
def add_registered_number(request):
    """Admin manually adds a registration number"""
    if request.method == 'POST':
        reg_number = request.POST.get('reg_number', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        level = request.POST.get('level', '100')
        
        if reg_number:
            obj, created = RegisteredRegNumber.objects.update_or_create(
                reg_number=reg_number,
                defaults={
                    'full_name': full_name if full_name else None,
                    'level': level,
                    'registered_by': request.user,
                    'is_active': True
                }
            )
            
            if created:
                messages.success(request, f'Successfully added registration number: {reg_number}')
            else:
                messages.success(request, f'Successfully updated registration number: {reg_number}')
        else:
            messages.error(request, 'Registration number is required')
        
        return redirect('manage_registered_numbers')
    
    return render(request, 'core/admin/add_registered_number.html')


@login_required
def delete_registered_number(request, pk):
    """Admin deletes a registration number"""
    number = get_object_or_404(RegisteredRegNumber, pk=pk)
    
    # Check if any student is using this reg number
    if Student.objects.filter(reg_number=pk).exists():
        messages.error(
            request, 
            f'Cannot delete {pk}. A student account already exists with this number.'
        )
        return redirect('manage_registered_numbers')
    
    if request.method == 'POST':
        number.delete()
        messages.success(request, f'Successfully deleted registration number: {pk}')
        return redirect('manage_registered_numbers')
    
    return render(request, 'core/admin/confirm_delete.html', {
        'object': number,
        'type': 'Registration Number'
    })


@login_required
def bulk_import_numbers(request):
    """Admin uploads CSV to bulk import registration numbers"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please upload a CSV file')
            return redirect('manage_registered_numbers')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File must be a CSV')
            return redirect('manage_registered_numbers')
        
        try:
            import csv
            from io import TextIOWrapper
            
            success_count = 0
            error_count = 0
            errors = []
            
            # Read CSV
            file_wrapper = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(file_wrapper)
            
            for row in reader:
                try:
                    reg_number = row.get('reg_number', '').strip()
                    full_name = row.get('full_name', '').strip()
                    level = row.get('level', '100').strip()
                    
                    if not reg_number:
                        continue
                    
                    RegisteredRegNumber.objects.update_or_create(
                        reg_number=reg_number,
                        defaults={
                            'full_name': full_name if full_name else None,
                            'level': level,
                            'registered_by': request.user,
                            'is_active': True
                        }
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row}: {str(e)}")
            
            if success_count > 0:
                messages.success(
                    request, 
                    f'Successfully imported {success_count} registration numbers'
                )
            
            if error_count > 0:
                messages.warning(
                    request,
                    f'{error_count} errors occurred. Check logs for details.'
                )
            
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
        
        return redirect('manage_registered_numbers')
    
    return render(request, 'core/admin/bulk_import_numbers.html')


@login_required
def view_payment_detail(request, pk):
    """View detailed payment information"""
    payment = get_object_or_404(StudentPayment, pk=pk)
    
    # Parse verification data if exists
    verification_data = None
    if payment.verification_data:
        import json
        try:
            verification_data = json.loads(payment.verification_data)
        except:
            pass
    
    context = {
        'payment': payment,
        'verification_data': verification_data,
    }
    return render(request, 'core/admin/payment_detail.html', context)


# Admin views for managing registration requests
@login_required
def manage_registration_requests(request):
    """Admin view to manage registration requests"""
    requests_list = RegistrationRequest.objects.all().order_by('-created_at')
    
    pending_count = requests_list.filter(status='pending').count()
    approved_count = requests_list.filter(status='approved').count()
    rejected_count = requests_list.filter(status='rejected').count()
    
    context = {
        'requests': requests_list,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'core/admin/manage_registration_requests.html', context)


@login_required
def approve_registration_request(request, pk):
    """Approve a registration request and add to registered numbers"""
    reg_request = get_object_or_404(RegistrationRequest, pk=pk)
    
    if request.method == 'POST':
        # Add to registered numbers
        RegisteredRegNumber.objects.create(
            reg_number=reg_request.reg_number,
            full_name=reg_request.full_name,
            level=reg_request.level,
            registered_by=request.user
        )
        
        # Update request status
        reg_request.status = 'approved'
        reg_request.reviewed_by = request.user
        reg_request.reviewed_at = timezone.now()
        reg_request.admin_notes = request.POST.get('notes', '')
        reg_request.save()
        
        messages.success(
            request,
            f'Registration request approved! {reg_request.reg_number} can now register.'
        )
        
        # TODO: Send email notification to student
        
        return redirect('manage_registration_requests')
    
    return render(request, 'core/admin/approve_registration_request.html', {
        'reg_request': reg_request
    })


@login_required
def reject_registration_request(request, pk):
    """Reject a registration request"""
    reg_request = get_object_or_404(RegistrationRequest, pk=pk)
    
    if request.method == 'POST':
        reg_request.status = 'rejected'
        reg_request.reviewed_by = request.user
        reg_request.reviewed_at = timezone.now()
        reg_request.admin_notes = request.POST.get('notes', '')
        reg_request.save()
        
        messages.success(request, 'Registration request rejected.')
        
        # TODO: Send email notification to student
        
        return redirect('manage_registration_requests')
    
    return render(request, 'core/admin/reject_registration_request.html', {
        'reg_request': reg_request
    })


@login_required
def manage_payments(request):
    """Admin view to see all payments"""
    payments = StudentPayment.objects.all().select_related('student').order_by('-created_at')
    
    total_revenue = payments.filter(status='success').aggregate(
        Sum('department_amount')
    )['department_amount__sum'] or 0
    
    context = {
        'payments': payments,
        'total_revenue': total_revenue,
        'total_payments': payments.filter(status='success').count(),
        'pending_payments': payments.filter(status='pending').count(),
    }
    return render(request, 'core/admin/manage_payments.html', context)

@student_required
def change_password(request):
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    if request.method == 'POST':
        form = PasswordChangeForm(student, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            student.set_password(new_password)
            student.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('student_profile')
    else:
        form = PasswordChangeForm(student)
    
    return render(request, 'core/student/change_password.html', {
        'form': form,
        'student': student
    })


# STUDENT DASHBOARD
@student_required
def student_dashboard(request):
    """Comprehensive student dashboard with all information"""
    from django.db.models import Sum, Count
    
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    # ==================== ACADEMIC STATISTICS ====================
    # CGPA Calculations
    semesters = student.semesters.all().prefetch_related('courses')
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
            'credits': semester_credits,
            'courses': courses
        })
    
    # Calculate overall CGPA
    cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    
    # Get latest CGPA calculation
    latest_cgpa = student.cgpa_calculations.first()
    
    # Get all CGPA history for trend
    cgpa_history = student.cgpa_calculations.all()[:10]
    
    # Academic Classification
    classification = "N/A"
    if cgpa >= 4.50:
        classification = "First Class"
    elif cgpa >= 3.50:
        classification = "Second Class Upper"
    elif cgpa >= 2.40:
        classification = "Second Class Lower"
    elif cgpa >= 1.50:
        classification = "Third Class"
    elif cgpa > 0:
        classification = "Pass"
    
    academic_stats = {
        'cgpa': cgpa,
        'total_credits': total_credits,
        'total_semesters': semesters.count(),
        'total_courses': sum(s['courses_count'] for s in semester_data),
        'classification': classification,
        'latest_calculation': latest_cgpa,
        'history_count': cgpa_history.count(),
    }
    
    # ==================== FINANCIAL STATUS ====================
    # Departmental Dues
    dues_status = {
        'exists': False,
        'is_approved': False,
        'amount_paid': 0,
        'receipt_number': None,
        'academic_session': None,
        'can_print': False,
    }
    
    try:
        dues = DepartmentalDues.objects.get(student=student)
        dues_status = {
            'exists': True,
            'is_approved': dues.is_approved,
            'amount_paid': dues.amount_paid,
            'receipt_number': dues.receipt_number,
            'academic_session': dues.academic_session,
            'can_print': dues.is_approved,
            'watermark_code': dues.watermark_code,
            'approved_at': dues.approved_at,
            'print_count': dues.print_count,
        }
    except DepartmentalDues.DoesNotExist:
        pass
    
    # Portal Payment Status
    portal_payment = {
        'has_paid': student.has_paid,
        'payment_verified_at': student.payment_verified_at,
    }
    
    try:
        payment = StudentPayment.objects.get(student=student)
        portal_payment['amount'] = payment.amount
        portal_payment['reference'] = payment.reference
        portal_payment['status'] = payment.status
        portal_payment['paid_at'] = payment.paid_at
    except StudentPayment.DoesNotExist:
        pass
    
    # ==================== RESEARCH CLUB STATUS ====================
    research_status = {
        'registered': False,
        'is_approved': False,
        'payment_status': None,
        'amount_paid': 0,
        'can_join_teams': False,
        'can_contribute': False,
    }
    
    try:
        registration = student.research_club_registration
        research_status = {
            'registered': True,
            'is_approved': registration.is_approved,
            'payment_status': registration.payment_status,
            'amount_paid': registration.amount_paid,
            'registered_at': registration.registered_at,
            'can_join_teams': registration.is_approved,
            'can_contribute': registration.is_approved,
            'payment_reference': registration.payment_reference,
        }
    except ResearchClubRegistration.DoesNotExist:
        pass
    
    # ==================== RESEARCH ACTIVITIES ====================
    # Team Memberships
    team_memberships = TeamMembership.objects.filter(
        student=student
    ).select_related('team')
    
    teams_data = []
    for membership in team_memberships:
        team = membership.team
        teams_data.append({
            'membership': membership,
            'team': team,
            'member_count': team.get_member_count(),
            'article_count': team.articles.count(),
            'published_count': team.articles.filter(status='Published').count(),
        })
    
    # Research Contributions
    contributions = ResearchContribution.objects.filter(
        student_contributor=student
    ).select_related('article', 'article__team')
    
    contributions_stats = {
        'total': contributions.count(),
        'approved': contributions.filter(is_approved=True).count(),
        'pending': contributions.filter(is_approved=False).count(),
        'by_article': contributions.values(
            'article__title', 'article__id'
        ).annotate(count=Count('id')),
    }
    
    # Quiz Activities
    quiz_submissions = QuizSubmission.objects.filter(
        student_submitter=student
    ).select_related('quiz')
    
    quiz_stats = {
        'total': quiz_submissions.count(),
        'awarded': quiz_submissions.filter(is_awarded=True).count(),
        'pending': quiz_submissions.filter(is_awarded=False).count(),
        'total_points': quiz_submissions.filter(
            is_awarded=True
        ).aggregate(
            total=Sum('quiz__points')
        )['total'] or 0,
    }
    
    # Article Interactions
    liked_articles = ArticleLike.objects.filter(
        student=student
    ).select_related('article')
    
    article_comments = ArticleComment.objects.filter(
        student=student
    ).select_related('article')
    
    interaction_stats = {
        'liked_count': liked_articles.count(),
        'comments_count': article_comments.count(),
        'articles_viewed': 0,  # This would require tracking
    }
    
    # ==================== ANNOUNCEMENTS & UPDATES ====================
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # ==================== ACADEMIC RESOURCES ====================
    # Resources for student's level
    past_questions = PastQuestion.objects.filter(
        level=student.level
    ).order_by('-year')[:5]
    
    library_resources = LibraryResource.objects.filter(
        Q(level=student.level) | Q(level__isnull=True)
    ).order_by('-created_at')[:5]
    
    # Course Handbook for current level
    course_handbook = CourseHandbook.objects.filter(
        level=student.level
    ).order_by('semester', 'course_code')
    
    first_semester_courses = course_handbook.filter(semester='First')
    second_semester_courses = course_handbook.filter(semester='Second')
    
    # Timetables
    current_timetables = Timetable.objects.filter(
        is_active=True,
        level__in=[student.level, 'All']
    ).order_by('-created_at')[:3]
    
    # Academic Calendar
    active_calendar = AcademicCalendar.objects.filter(is_active=True).first()
    
    resources_stats = {
        'past_questions_count': PastQuestion.objects.filter(level=student.level).count(),
        'library_resources_count': LibraryResource.objects.filter(
            Q(level=student.level) | Q(level__isnull=True)
        ).count(),
        'first_sem_courses': first_semester_courses.count(),
        'second_sem_courses': second_semester_courses.count(),
        'timetables_available': current_timetables.count(),
        'calendar_available': active_calendar is not None,
    }
    
    # ==================== QUICK STATS SUMMARY ====================
    quick_stats = {
        'cgpa': cgpa,
        'classification': classification,
        'semesters': semesters.count(),
        'total_credits': total_credits,
        'research_teams': team_memberships.count(),
        'contributions': contributions_stats['total'],
        'quiz_points': quiz_stats['total_points'],
        'liked_articles': interaction_stats['liked_count'],
    }
    
    # ==================== ACTIVITY SUMMARY ====================
    activity_summary = {
        'last_login': student.updated_at,
        'cgpa_calculations': student.cgpa_calculations.count(),
        'semesters_added': semesters.count(),
        'recent_contribution': contributions.order_by('-created_at').first(),
        'recent_quiz': quiz_submissions.order_by('-created_at').first(),
        'dues_status': 'Approved' if dues_status['is_approved'] else 'Pending' if dues_status['exists'] else 'Not Paid',
        'research_status': 'Active' if research_status['is_approved'] else 'Pending' if research_status['registered'] else 'Not Registered',
    }
    
    # ==================== RECOMMENDATIONS ====================
    recommendations = []
    
    # Academic recommendations
    if semesters.count() == 0:
        recommendations.append({
            'type': 'academic',
            'icon': 'calculator',
            'title': 'Start CGPA Tracking',
            'message': 'Add your first semester to start tracking your CGPA',
            'action': 'Add Semester',
            'url': 'add_semester'
        })
    
    if cgpa > 0 and cgpa < 2.40:
        recommendations.append({
            'type': 'warning',
            'icon': 'exclamation-triangle',
            'title': 'Academic Support Needed',
            'message': f'Your current CGPA ({cgpa}) is below Second Class Lower. Consider academic support.',
            'action': 'View Resources',
            'url': 'library'
        })
    
    # Financial recommendations
    if not dues_status['exists']:
        recommendations.append({
            'type': 'info',
            'icon': 'receipt',
            'title': 'Pay Departmental Dues',
            'message': 'Complete your departmental dues payment to get your receipt',
            'action': 'Contact Admin',
            'url': '#'
        })
    
    # Research recommendations
    if not research_status['registered']:
        recommendations.append({
            'type': 'research',
            'icon': 'flask',
            'title': 'Join Research Club',
            'message': 'Register for the research club to join teams and contribute to articles',
            'action': 'Register Now',
            'url': 'research_club_register'
        })
    elif research_status['is_approved'] and team_memberships.count() == 0:
        recommendations.append({
            'type': 'research',
            'icon': 'users',
            'title': 'Join a Research Team',
            'message': 'Explore available teams and start contributing to research',
            'action': 'Browse Teams',
            'url': 'research_hub'
        })
    
    # Quiz recommendations
    if research_status['is_approved']:
        active_quizzes = ResearchQuiz.objects.filter(is_active=True).exclude(
            submissions__student_submitter=student
        ).count()
        
        if active_quizzes > 0:
            recommendations.append({
                'type': 'quiz',
                'icon': 'trophy',
                'title': 'Active Quizzes Available',
                'message': f'{active_quizzes} quiz(zes) available. Test your knowledge and earn points!',
                'action': 'View Quizzes',
                'url': 'research_quizzes'
            })
    
    # ==================== COMPILE CONTEXT ====================
    context = {
        'student': student,
        'quick_stats': quick_stats,
        'academic_stats': academic_stats,
        'semesters': semester_data,
        'cgpa_history': cgpa_history,
        'dues_status': dues_status,
        'portal_payment': portal_payment,
        'research_status': research_status,
        'teams_data': teams_data,
        'contributions_stats': contributions_stats,
        'quiz_stats': quiz_stats,
        'interaction_stats': interaction_stats,
        'announcements': announcements,
        'past_questions': past_questions,
        'library_resources': library_resources,
        'first_semester_courses': first_semester_courses,
        'second_semester_courses': second_semester_courses,
        'current_timetables': current_timetables,
        'active_calendar': active_calendar,
        'resources_stats': resources_stats,
        'activity_summary': activity_summary,
        'recommendations': recommendations,
        'latest_cgpa': latest_cgpa,
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
@financial_access_required
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
@financial_access_required
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
@financial_access_required
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
@financial_access_required
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
    """Enhanced print receipt with security logging"""
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    try:
        dues = DepartmentalDues.objects.get(student=student, is_approved=True)
    except DepartmentalDues.DoesNotExist:
        messages.error(request, 'Your departmental dues have not been approved yet.')
        return redirect('my_receipt')
    
    # Log the print event
    ReceiptPrintLog.objects.create(
        receipt=dues,
        printed_by_student=student,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Increment print count
    dues.increment_print_count()
    
    # Log security event
    logger.info(f"Receipt {dues.receipt_number} printed by {student.reg_number} from IP {get_client_ip(request)}")
    
    context = {
        'student': student,
        'dues': dues,
        'security_verified': True,
        'print_number': dues.print_count,
        'current_timestamp': timezone.now()
    }
    
    return render(request, 'core/student/print_receipt.html', context)


@require_http_methods(["GET", "POST"])
def verify_receipt(request):
    """Public API endpoint for receipt verification"""
    if request.method == 'GET':
        return render(request, 'core/verify_receipt.html')
    
    # POST request - verify the receipt
    verification_code = request.POST.get('verification_code', '').strip()
    receipt_number = request.POST.get('receipt_number', '').strip()
    
    result = {
        'is_valid': False,
        'message': 'Invalid verification code',
        'details': None
    }
    
    try:
        if verification_code:
            # Try to find by watermark code
            dues = DepartmentalDues.objects.get(watermark_code=verification_code, is_approved=True)
        elif receipt_number:
            # Try to find by receipt number
            dues = DepartmentalDues.objects.get(receipt_number=receipt_number, is_approved=True)
        else:
            raise DepartmentalDues.DoesNotExist
        
        # Log verification attempt
        ReceiptVerification.objects.create(
            receipt=dues,
            verification_code=verification_code or receipt_number,
            is_valid=True,
            ip_address=get_client_ip(request)
        )
        
        result = {
            'is_valid': True,
            'message': 'Receipt is authentic and valid',
            'details': {
                'receipt_number': dues.receipt_number,
                'student_name': dues.student.full_name,
                'student_reg': dues.student.reg_number,
                'amount_paid': str(dues.amount_paid),
                'academic_session': dues.academic_session,
                'approved_date': dues.approved_at.strftime('%Y-%m-%d'),
                'verification_code': dues.watermark_code,
                'print_count': dues.print_count
            }
        }
        
        logger.info(f"Receipt {dues.receipt_number} verified successfully from IP {get_client_ip(request)}")
        
    except DepartmentalDues.DoesNotExist:
        # Log failed verification attempt
        ReceiptVerification.objects.create(
            verification_code=verification_code or receipt_number,
            is_valid=False,
            ip_address=get_client_ip(request)
        )
        
        logger.warning(f"Failed receipt verification attempt for code: {verification_code or receipt_number} from IP {get_client_ip(request)}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(result)
    
    return render(request, 'core/verify_receipt.html', {'result': result})

@login_required
def admin_receipt_analytics(request):
    """Admin view for receipt analytics and fraud detection"""
    # Get suspicious activities
    suspicious_prints = ReceiptPrintLog.objects.values('receipt__receipt_number', 'ip_address').annotate(
        print_count=Count('id')
    ).filter(print_count__gt=10).order_by('-print_count')
    
    failed_verifications = ReceiptVerification.objects.filter(
        is_valid=False
    ).values('ip_address').annotate(
        attempt_count=Count('id')
    ).filter(attempt_count__gt=5).order_by('-attempt_count')
    
    # Recent prints
    recent_prints = ReceiptPrintLog.objects.select_related('receipt', 'printed_by_student').order_by('-printed_at')[:50]
    
    # Statistics
    stats = {
        'total_receipts': DepartmentalDues.objects.filter(is_approved=True).count(),
        'total_prints': ReceiptPrintLog.objects.count(),
        'total_verifications': ReceiptVerification.objects.filter(is_valid=True).count(),
        'failed_verifications': ReceiptVerification.objects.filter(is_valid=False).count(),
        'avg_prints_per_receipt': ReceiptPrintLog.objects.values('receipt').annotate(
            Count('id')
        ).aggregate(Avg('id__count'))['id__count__avg'] or 0
    }
    
    context = {
        'suspicious_prints': suspicious_prints,
        'failed_verifications': failed_verifications,
        'recent_prints': recent_prints,
        'stats': stats
    }
    
    return render(request, 'core/admin/receipt_analytics.html', context)


@login_required
def revoke_receipt(request, pk):
    """Admin can revoke a receipt if fraud is detected"""
    dues = get_object_or_404(DepartmentalDues, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('revoke_reason', '')
        
        # Mark as unapproved
        dues.is_approved = False
        dues.save()
        
        # Log the revocation
        logger.warning(f"Receipt {dues.receipt_number} revoked by {request.user.username}. Reason: {reason}")
        
        messages.success(request, f'Receipt {dues.receipt_number} has been revoked.')
        return redirect('manage_departmental_dues')
    
    return render(request, 'core/admin/revoke_receipt.html', {'dues': dues})


# API endpoint for mobile app verification
@require_http_methods(["POST"])
def api_verify_receipt(request):
    """API endpoint for mobile verification"""
    import json
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        
        dues = DepartmentalDues.objects.get(
            watermark_code=code,
            is_approved=True
        )
        
        # Log verification
        ReceiptVerification.objects.create(
            receipt=dues,
            verification_code=code,
            is_valid=True,
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'status': 'success',
            'valid': True,
            'data': {
                'receipt_number': dues.receipt_number,
                'student': dues.student.full_name,
                'reg_number': dues.student.reg_number,
                'amount': str(dues.amount_paid),
                'session': dues.academic_session,
                'approved_date': dues.approved_at.isoformat()
            }
        })
        
    except DepartmentalDues.DoesNotExist:
        # Log failed attempt
        ReceiptVerification.objects.create(
            verification_code=code,
            is_valid=False,
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'status': 'error',
            'valid': False,
            'message': 'Invalid or unrecognized verification code'
        }, status=404)
        
    except Exception as e:
        logger.error(f"API verification error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Verification service error'
        }, status=500)

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

def research_club_required(view_func):
    """Decorator to check if student has paid and been approved for research club"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('student_reg_number'):
            messages.error(request, 'Please login first.')
            return redirect('student_login')
        
        reg_number = request.session.get('student_reg_number')
        student = Student.objects.get(reg_number=reg_number)
        
        # Check if registered and approved for research club
        try:
            registration = student.research_club_registration
            if not registration.is_approved:
                messages.warning(
                    request, 
                    'Please register for the research club to access this feature. '
                    'Registration fee: ₦1,000'
                )
                return redirect('research_club_register')
        except ResearchClubRegistration.DoesNotExist:
            messages.warning(
                request,
                'Please register for the research club to join teams. '
                'Registration fee: ₦1,000'
            )
            return redirect('research_club_register')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@research_club_required
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




@student_required
def research_club_register(request):
    """Student registers for research club with manual payment"""
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    # Check if already registered
    if hasattr(student, 'research_club_registration'):
        registration = student.research_club_registration
        if registration.is_approved:
            messages.info(request, 'You are already a research club member!')
            return redirect('research_hub')
        elif registration.payment_status == 'pending':
            messages.warning(request, 'Your registration is pending verification.')
            return redirect('research_club_status')
    
    if request.method == 'POST':
        form = ResearchClubRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.student = student
            registration.amount_paid = 1000.00
            registration.payment_status = 'pending'
            registration.save()
            
            messages.success(
                request,
                'Registration submitted! Your payment proof is being verified. '
                'You will be notified once approved.'
            )
            return redirect('research_club_status')
    else:
        form = ResearchClubRegistrationForm()
    
    context = {
        'form': form,
        'student': student,
        'account_number': '9071720720',
        'bank_name': 'Moniepoint',
        'account_name': 'Julius Omolara',
        'amount': 1000,
    }
    return render(request, 'core/research/club_register.html', context)


@student_required
def research_club_status(request):
    """Check registration status"""
    reg_number = request.session.get('student_reg_number')
    student = Student.objects.get(reg_number=reg_number)
    
    try:
        registration = student.research_club_registration
    except ResearchClubRegistration.DoesNotExist:
        messages.error(request, 'You have not registered yet.')
        return redirect('research_club_register')
    
    context = {
        'registration': registration,
        'student': student,
    }
    return render(request, 'core/research/club_status.html', context)


# ADMIN VIEWS

@login_required
def manage_research_registrations(request):
    """Admin verifies and approves registrations"""
    registrations = ResearchClubRegistration.objects.all().select_related('student').order_by('-registered_at')
    
    pending = registrations.filter(payment_status='pending')
    verified = registrations.filter(payment_status='verified', is_approved=True)
    rejected = registrations.filter(payment_status='rejected')
    
    context = {
        'registrations': registrations,
        'pending_count': pending.count(),
        'verified_count': verified.count(),
        'rejected_count': rejected.count(),
    }
    return render(request, 'core/admin/manage_research_registrations.html', context)



@login_required
def verify_research_payment(request, pk):
    """Admin verifies payment proof"""
    registration = get_object_or_404(ResearchClubRegistration, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            registration.payment_status = 'verified'
            registration.is_approved = True
            registration.approved_by = request.user
            registration.approved_at = timezone.now()
            registration.save()
            
            messages.success(
                request,
                f'Payment verified for {registration.student.full_name}! '
                f'They can now access research features.'
            )
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            registration.payment_status = 'rejected'
            registration.rejection_reason = reason
            registration.save()
            
            messages.success(request, 'Registration rejected.')
        
        return redirect('manage_research_registrations')
    
    context = {
        'registration': registration,
    }
    return render(request, 'core/admin/verify_research_payment.html', context)

@login_required
def manage_guest_payments(request):
    """Admin manages guest contributor payments"""
    guests = GuestContributor.objects.all().order_by('-created_at')
    
    pending = guests.filter(payment_status='pending')
    approved = guests.filter(is_approved=True)
    
    context = {
        'guests': guests,
        'pending_count': pending.count(),
        'approved_count': approved.count(),
    }
    return render(request, 'core/admin/manage_guest_payments.html', context)


@login_required
def verify_guest_payment(request, pk):
    """Admin verifies guest payment"""
    guest = get_object_or_404(GuestContributor, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            guest.payment_status = 'verified'
            guest.is_approved = True
            guest.approved_by = request.user
            guest.approved_at = timezone.now()
            guest.save()
            
            messages.success(
                request,
                f'{guest.full_name} approved as guest contributor!'
            )
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            guest.payment_status = 'rejected'
            guest.rejection_reason = reason
            guest.save()
            
            messages.success(request, 'Guest application rejected.')
        
        return redirect('manage_guest_payments')
    
    context = {
        'guest': guest,
    }
    return render(request, 'core/admin/verify_guest_payment.html', context)