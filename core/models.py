from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.core.validators import FileExtensionValidator
import uuid
import json

class Staff(models.Model):
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    bio = models.TextField()
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    image = CloudinaryField('image', blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.name} - {self.position}"


class Exco(models.Model):
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    bio = models.TextField()
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    image = CloudinaryField('image', blank=True, null=True)
    session = models.CharField(max_length=50, help_text="e.g., 2023/2024")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Excos"

    def __str__(self):
        return f"{self.name} - {self.position} ({self.session})"


class PastQuestion(models.Model):
    SEMESTER_CHOICES = [
        ('First', 'First Semester'),
        ('Second', 'Second Semester'),
    ]
    
    LEVEL_CHOICES = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
    ]

    course_code = models.CharField(max_length=20)
    course_title = models.CharField(max_length=200)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    year = models.IntegerField()
    link = models.URLField(help_text="Google Drive, Dropbox, or any other link to the file")
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'level', 'course_code']

    def __str__(self):
        return f"{self.course_code} - {self.year} ({self.semester} Semester)"


class LibraryResource(models.Model):
    CATEGORY_CHOICES = [
        ('Textbook', 'Textbook'),
        ('Journal', 'Journal Article'),
        ('Lecture', 'Lecture Notes'),
        ('Project', 'Project Report'),
        ('Thesis', 'Thesis'),
        ('Other', 'Other'),
    ]

    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    link = models.URLField(help_text="Link to the resource")
    cover_image = CloudinaryField('image', blank=True, null=True)
    level = models.CharField(max_length=10, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.IntegerField(default=5, help_text="Rating out of 5")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {'Approved' if self.is_approved else 'Pending'}"


class Announcement(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# NEW STUDENT MODELS
class Student(models.Model):
    LEVEL_CHOICES = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
    ]

    reg_number = models.CharField(max_length=50, unique=True, primary_key=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='100')
    profile_image = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reg_number']

    def __str__(self):
        return f"{self.reg_number} - {self.full_name}"


class Semester(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=100, help_text="e.g., 100 Level First Semester")
    year = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['student', 'name']

    def __str__(self):
        return f"{self.student.reg_number} - {self.name}"

    def calculate_gpa(self):
        """Calculate GPA for this semester"""
        courses = self.courses.all()
        if not courses:
            return 0.0
        
        total_credits = sum(course.credit_unit for course in courses)
        if total_credits == 0:
            return 0.0
        
        total_points = sum(course.credit_unit * course.grade_point for course in courses)
        return round(total_points / total_credits, 2)


class Course(models.Model):
    GRADE_CHOICES = [
        (5.0, 'A (5.0)'),
        (4.0, 'B (4.0)'),
        (3.0, 'C (3.0)'),
        (2.0, 'D (2.0)'),
        (1.0, 'E (1.0)'),
        (0.0, 'F (0.0)'),
    ]

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=200)
    credit_unit = models.IntegerField()
    grade_point = models.FloatField(choices=GRADE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course_code']

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

    def get_grade_letter(self):
        """Return grade letter based on grade point"""
        grade_map = {5.0: 'A', 4.0: 'B', 3.0: 'C', 2.0: 'D', 1.0: 'E', 0.0: 'F'}
        return grade_map.get(self.grade_point, 'N/A')


class CGPACalculation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='cgpa_calculations')
    cgpa = models.FloatField()
    total_credit_units = models.IntegerField()
    total_grade_points = models.FloatField()
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calculated_at']

    def __str__(self):
        return f"{self.student.reg_number} - CGPA: {self.cgpa}"


# DEPARTMENTAL DUES RECEIPT MODEL
class DepartmentalDues(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='departmental_dues')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    payment_reference = models.CharField(max_length=100, unique=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text="Admin approval required")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_dues')
    approved_at = models.DateTimeField(null=True, blank=True)
    academic_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    watermark_code = models.CharField(max_length=100, blank=True, help_text="Unique code for verification")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Departmental Dues"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate unique receipt number: BME/2024/001
            import datetime
            year = datetime.datetime.now().year
            last_receipt = DepartmentalDues.objects.filter(
                receipt_number__startswith=f'BME/{year}/'
            ).order_by('-receipt_number').first()
            
            if last_receipt:
                last_number = int(last_receipt.receipt_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.receipt_number = f'BME/{year}/{new_number:04d}'
        
        if not self.watermark_code:
            # Generate unique watermark code for anti-fraud
            self.watermark_code = f"BME-{uuid.uuid4().hex[:12].upper()}"
        
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.reg_number} - {self.receipt_number}"


# COURSE HANDBOOK MODEL
class CourseHandbook(models.Model):
    LEVEL_CHOICES = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
    ]
    
    SEMESTER_CHOICES = [
        ('First', 'First Semester'),
        ('Second', 'Second Semester'),
    ]
    
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    course_code = models.CharField(max_length=20)
    course_title = models.CharField(max_length=300)
    credit_unit = models.IntegerField()
    course_type = models.CharField(max_length=20, choices=[
        ('Core', 'Core'),
        ('Required', 'Required'),
        ('Elective', 'Elective'),
    ], default='Core')
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level', 'semester', 'course_code']
        unique_together = ['level', 'semester', 'course_code']
        verbose_name_plural = "Course Handbook"
    
    def __str__(self):
        return f"{self.level}L {self.semester} - {self.course_code}"


# TIMETABLE MODEL
class Timetable(models.Model):
    TIMETABLE_CHOICES = [
        ('Exam', 'Examination Timetable'),
        ('Class', 'Class Timetable'),
    ]
    
    LEVEL_CHOICES = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
        ('All', 'All Levels'),
    ]
    
    SEMESTER_CHOICES = [
        ('First', 'First Semester'),
        ('Second', 'Second Semester'),
    ]
    
    title = models.CharField(max_length=300)
    timetable_type = models.CharField(max_length=10, choices=TIMETABLE_CHOICES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='All')
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    academic_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    image = CloudinaryField('image', 
                           validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])],
                           help_text="Upload timetable image or PDF")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Timetables"
    
    def __str__(self):
        return f"{self.timetable_type} - {self.level} {self.semester} ({self.academic_session})"


# ACADEMIC CALENDAR MODEL
class AcademicCalendar(models.Model):
    title = models.CharField(max_length=300)
    academic_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    image = CloudinaryField('image',
                           validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])],
                           help_text="Upload academic calendar image or PDF")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Only one calendar should be active at a time")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Academic Calendars"
    
    def __str__(self):
        return f"{self.title} ({self.academic_session})"
    
    def save(self, *args, **kwargs):
        # If this calendar is being set as active, deactivate all others
        if self.is_active:
            AcademicCalendar.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)