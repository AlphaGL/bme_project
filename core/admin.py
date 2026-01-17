from django.contrib import admin
from .models import (
    Staff, Exco, PastQuestion, LibraryResource, 
    Testimonial, Announcement, Student, Semester, 
    Course, CGPACalculation, DepartmentalDues, CourseHandbook, Timetable, AcademicCalendar,    ResearchTeam, ResearchArticle, GuestContributor, ResearchContribution,
    ResearchQuiz, QuizSubmission, TeamMembership, ArticleLike, AccessPin, PinUsageLog
)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'email', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'position', 'email']
    ordering = ['order', 'name']

@admin.register(Exco)
class ExcoAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'session', 'is_msrc', 'email', 'order', 'created_at']
    list_filter = ['session', 'is_msrc', 'created_at']
    search_fields = ['name', 'position', 'email']
    ordering = ['order', 'name']
    
    # Group fields logically
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'bio')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone')
        }),
        ('Session & Role', {
            'fields': ('session', 'is_msrc')
        }),
        ('Display Settings', {
            'fields': ('image', 'order')
        }),
    )

@admin.register(PastQuestion)
class PastQuestionAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_title', 'level', 'semester', 'year', 'uploaded_by', 'created_at']
    list_filter = ['level', 'semester', 'year']
    search_fields = ['course_code', 'course_title']
    ordering = ['-year', 'level', 'course_code']

@admin.register(LibraryResource)
class LibraryResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'level', 'uploaded_by', 'created_at']
    list_filter = ['category', 'level', 'created_at']
    search_fields = ['title', 'author']
    ordering = ['-created_at']

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['name', 'message']
    actions = ['approve_testimonials', 'unapprove_testimonials']
    
    def approve_testimonials(self, request, queryset):
        queryset.update(is_approved=True)
    approve_testimonials.short_description = "Approve selected testimonials"
    
    def unapprove_testimonials(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_testimonials.short_description = "Unapprove selected testimonials"

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']


# STUDENT PORTAL ADMIN
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['reg_number', 'full_name', 'email', 'level', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['reg_number', 'full_name', 'email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('reg_number', 'full_name', 'email', 'phone')
        }),
        ('Academic Information', {
            'fields': ('level', 'profile_image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['student', 'name', 'year', 'courses_count', 'created_at']
    list_filter = ['created_at', 'year']
    search_fields = ['student__reg_number', 'student__full_name', 'name']
    ordering = ['-created_at']
    
    def courses_count(self, obj):
        return obj.courses.count()
    courses_count.short_description = 'Courses'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'semester', 'credit_unit', 'grade_point', 'created_at']
    list_filter = ['grade_point', 'credit_unit', 'created_at']
    search_fields = ['course_code', 'course_name', 'semester__student__reg_number']
    ordering = ['-created_at']


@admin.register(CGPACalculation)
class CGPACalculationAdmin(admin.ModelAdmin):
    list_display = ['student', 'cgpa', 'total_credit_units', 'total_grade_points', 'calculated_at']
    list_filter = ['calculated_at']
    search_fields = ['student__reg_number', 'student__full_name']
    ordering = ['-calculated_at']
    readonly_fields = ['student', 'cgpa', 'total_credit_units', 'total_grade_points', 'calculated_at']
    
    def has_add_permission(self, request):
        # Prevent manual addition through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Make read-only
        return False


@admin.register(DepartmentalDues)
class DepartmentalDuesAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'amount_paid', 'is_approved', 'academic_session', 'created_at']
    list_filter = ['is_approved', 'academic_session', 'created_at']
    search_fields = ['student__reg_number', 'student__full_name', 'receipt_number', 'payment_reference']
    readonly_fields = ['receipt_number', 'watermark_code', 'payment_reference', 'created_at', 'updated_at', 'approved_at']
    actions = ['approve_dues', 'unapprove_dues']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'academic_session')
        }),
        ('Payment Details', {
            'fields': ('amount_paid', 'payment_reference')
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
        ('Receipt Information', {
            'fields': ('receipt_number', 'watermark_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_dues(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_approved=True, approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{updated} dues approved successfully.')
    approve_dues.short_description = "Approve selected dues"
    
    def unapprove_dues(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_by=None, approved_at=None)
        self.message_user(request, f'{updated} dues unapproved.')
    unapprove_dues.short_description = "Unapprove selected dues"


@admin.register(CourseHandbook)
class CourseHandbookAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_title', 'level', 'semester', 'credit_unit', 'course_type', 'created_at']
    list_filter = ['level', 'semester', 'course_type', 'created_at']
    search_fields = ['course_code', 'course_title']
    ordering = ['level', 'semester', 'course_code']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course_code', 'course_title', 'credit_unit', 'course_type')
        }),
        ('Classification', {
            'fields': ('level', 'semester')
        }),
        ('Additional Details', {
            'fields': ('description', 'uploaded_by')
        }),
    )


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['title', 'timetable_type', 'level', 'semester', 'academic_session', 'is_active', 'created_at']
    list_filter = ['timetable_type', 'level', 'semester', 'is_active', 'academic_session', 'created_at']
    search_fields = ['title', 'academic_session']
    ordering = ['-created_at']


@admin.register(AcademicCalendar)
class AcademicCalendarAdmin(admin.ModelAdmin):
    list_display = ['title', 'academic_session', 'is_active', 'created_at']
    list_filter = ['is_active', 'academic_session', 'created_at']
    search_fields = ['title', 'academic_session']
    ordering = ['-created_at']
    
    def save_model(self, request, obj, form, change):
        obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ResearchTeam)
class ResearchTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'focus_area', 'team_lead', 'is_active', 'get_member_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'focus_area']
    ordering = ['name']


@admin.register(ResearchArticle)
class ResearchArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'status', 'views_count', 'likes_count', 'created_at']
    list_filter = ['status', 'team', 'created_at']
    search_fields = ['title', 'abstract']
    ordering = ['-created_at']


@admin.register(GuestContributor)
class GuestContributorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'institution', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['full_name', 'email', 'institution']
    readonly_fields = ['password', 'approved_at', 'created_at']
    actions = ['approve_guests', 'unapprove_guests']
    
    def approve_guests(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_approved=True, approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{updated} guest contributors approved.')
    approve_guests.short_description = "Approve selected guest contributors"
    
    def unapprove_guests(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_by=None, approved_at=None)
        self.message_user(request, f'{updated} guest contributors unapproved.')
    unapprove_guests.short_description = "Unapprove selected guest contributors"


@admin.register(ResearchContribution)
class ResearchContributionAdmin(admin.ModelAdmin):
    list_display = ['get_contributor_name', 'section_title', 'article', 'is_approved', 'section_order', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['section_title', 'content', 'student_contributor__full_name', 'guest_contributor__full_name']
    readonly_fields = ['approved_at', 'created_at', 'updated_at']
    actions = ['approve_contributions', 'unapprove_contributions']
    
    def get_contributor_name(self, obj):
        """Display contributor name in admin list"""
        return obj.get_contributor_name()
    get_contributor_name.short_description = 'Contributor'
    
    def approve_contributions(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_approved=True, approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{updated} contributions approved.')
    approve_contributions.short_description = "Approve selected contributions"
    
    def unapprove_contributions(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_by=None, approved_at=None)
        self.message_user(request, f'{updated} contributions unapproved.')
    unapprove_contributions.short_description = "Unapprove selected contributions"


@admin.register(ResearchQuiz)
class ResearchQuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty_level', 'points', 'is_active', 'get_submissions_count', 'created_at']
    list_filter = ['is_active', 'difficulty_level', 'created_at']
    search_fields = ['title', 'question', 'category']
    ordering = ['-created_at']


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ['get_submitter_name', 'quiz', 'is_awarded', 'awarded_at', 'created_at']
    list_filter = ['is_awarded', 'created_at']
    search_fields = ['answer', 'explanation', 'student_submitter__full_name', 'guest_submitter__full_name']
    readonly_fields = ['awarded_at', 'created_at', 'updated_at']
    actions = ['award_submissions']
    
    def get_submitter_name(self, obj):
        """Display submitter name in admin list"""
        return obj.get_submitter_name()
    get_submitter_name.short_description = 'Submitter'
    
    def award_submissions(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_awarded=True, awarded_by=request.user, awarded_at=timezone.now())
        self.message_user(request, f'{updated} submissions awarded.')
    award_submissions.short_description = "Award selected submissions"

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['student', 'team', 'role', 'joined_at']
    list_filter = ['team', 'joined_at']
    search_fields = ['student__full_name', 'student__reg_number', 'team__name']
    ordering = ['-joined_at']


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ['student', 'article', 'created_at']
    list_filter = ['created_at']
    search_fields = ['student__full_name', 'article__title']
    ordering = ['-created_at']


# Add to existing admin.py

@admin.register(AccessPin)
class AccessPinAdmin(admin.ModelAdmin):
    list_display = ['pin', 'status', 'batch_number', 'used_by', 'generated_at', 'expires_at']
    list_filter = ['status', 'generated_at', 'batch_number']
    search_fields = ['pin', 'used_by__full_name', 'used_by__reg_number', 'batch_number']
    readonly_fields = ['pin', 'generated_by', 'generated_at', 'used_by', 'used_at']
    ordering = ['-generated_at']
    
    fieldsets = (
        ('PIN Information', {
            'fields': ('pin', 'status', 'batch_number')
        }),
        ('Generation Details', {
            'fields': ('generated_by', 'generated_at', 'expires_at')
        }),
        ('Usage Details', {
            'fields': ('used_by', 'used_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent manual addition - use generation view instead
        return False


@admin.register(PinUsageLog)
class PinUsageLogAdmin(admin.ModelAdmin):
    list_display = ['pin', 'student_reg_number', 'attempt_successful', 'attempted_at', 'ip_address']
    list_filter = ['attempt_successful', 'attempted_at']
    search_fields = ['pin__pin', 'student_reg_number', 'ip_address']
    readonly_fields = ['pin', 'student_reg_number', 'attempt_successful', 'attempted_at', 'ip_address', 'user_agent', 'error_message']
    ordering = ['-attempted_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False