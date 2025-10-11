from django.contrib import admin
from .models import (
    Staff, Exco, PastQuestion, LibraryResource, 
    Testimonial, Announcement, Student, Semester, 
    Course, CGPACalculation
)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'email', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'position', 'email']
    ordering = ['order', 'name']

@admin.register(Exco)
class ExcoAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'session', 'email', 'order', 'created_at']
    list_filter = ['session', 'created_at']
    search_fields = ['name', 'position', 'email']
    ordering = ['order', 'name']

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