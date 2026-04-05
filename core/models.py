from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.core.validators import FileExtensionValidator
import uuid
from django.contrib.auth.hashers import make_password, check_password
import hashlib
from django.utils import timezone
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
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    image = CloudinaryField('image', blank=True, null=True)
    session = models.CharField(max_length=50, help_text="e.g., 2023/2024")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    
    # NEW: MSRC field
    is_msrc = models.BooleanField(
        default=False, 
        help_text="Check if this person is a Member of Student Representative Council (MSRC)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Excos"

    def __str__(self):
        msrc_tag = " (MSRC)" if self.is_msrc else ""
        return f"{self.name} - {self.position} ({self.session}){msrc_tag}"


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
    year = models.IntegerField(blank=True, null=True)
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
        ('Constitution', 'Nabes Constitution'),
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
    has_paid = models.BooleanField(default=False)
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    profile_image = CloudinaryField('image', blank=True, null=True)
    
    # NEW: Add password field
    password = models.CharField(max_length=128, help_text="Hashed password")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reg_number']


    PAYMENT_METHOD_CHOICES = [
        ('paystack', 'Paystack Payment'),
        ('pin', 'Access PIN'),
    ]
    
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        null=True, 
        blank=True,
        help_text="How the student paid for portal access"
    )
    
    access_pin_used = models.ForeignKey(
        'AccessPin', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='registered_student'
    )

    def __str__(self):
        return f"{self.reg_number} - {self.full_name}"
    
    # NEW: Password methods
    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the provided password is correct"""
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        # If this is a new student and no password is set, use reg_number as default
        if not self.pk and not self.password:
            self.set_password(self.reg_number)
        super().save(*args, **kwargs)


# Add these new models to your existing models.py

class RegisteredRegNumber(models.Model):
    """Store registered BME student registration numbers"""
    reg_number = models.CharField(max_length=50, unique=True, primary_key=True)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    level = models.CharField(max_length=10, choices=Student.LEVEL_CHOICES)
    date_registered = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['reg_number']
        verbose_name_plural = "Registered Registration Numbers"
    
    def __str__(self):
        return f"{self.reg_number} - {self.full_name or 'Not Assigned'}"


class RegistrationRequest(models.Model):
    """Handle registration requests from students not in the system"""
    reg_number = models.CharField(max_length=50)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    level = models.CharField(max_length=10, choices=Student.LEVEL_CHOICES)
    reason = models.TextField(help_text="Why you should be added")
    proof_document = CloudinaryField('document', blank=True, null=True, 
                                     help_text="Upload proof (admission letter, ID card, etc)")
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Registration Requests"
    
    def __str__(self):
        return f"{self.reg_number} - {self.full_name} ({self.status})"


class StudentPayment(models.Model):
    """Track student payments for portal access"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='payment')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1250.00)
    department_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=250.00)
    
    # Paystack details
    reference = models.CharField(max_length=100, unique=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    access_code = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    paid_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_data = models.TextField(blank=True, null=True)  # Store JSON response
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Student Payments"
    
    def __str__(self):
        return f"{self.student.reg_number} - {self.reference} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Always generate a new reference (don't check if it exists)
        import uuid
        self.reference = f"BME-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
        

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


class DepartmentalDues(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='departmental_dues')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    payment_reference = models.CharField(max_length=100, unique=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text="Admin approval required")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_dues')
    approved_at = models.DateTimeField(null=True, blank=True)
    academic_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    watermark_code = models.CharField(max_length=100, blank=True, help_text="Unique code for verification")
    
    # ENHANCED SECURITY FIELDS
    security_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash for verification")
    qr_code_data = models.TextField(blank=True, help_text="QR code data for verification")
    print_count = models.IntegerField(default=0, help_text="Number of times receipt was printed")
    last_printed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of payment submission")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Departmental Dues"
    
    def generate_security_hash(self):
        """Generate a unique security hash for this receipt"""
        data = f"{self.student.reg_number}{self.receipt_number}{self.watermark_code}{self.amount_paid}{self.academic_session}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generate_qr_data(self):
        """Generate QR code data for verification"""
        return f"VERIFY:{self.receipt_number}:{self.watermark_code}:{self.security_hash[:16]}"
    
    def verify_authenticity(self, provided_hash):
        """Verify if the receipt is authentic"""
        return self.security_hash == provided_hash
    
    def increment_print_count(self):
        """Track printing for audit purposes"""
        self.print_count += 1
        self.last_printed_at = timezone.now()
        self.save(update_fields=['print_count', 'last_printed_at'])
    
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
            # Generate unique watermark code with timestamp
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            random_part = uuid.uuid4().hex[:8].upper()
            self.watermark_code = f"BME-{timestamp}-{random_part}"
        
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        
        # Generate security features
        if not self.security_hash:
            self.security_hash = self.generate_security_hash()
        
        if not self.qr_code_data:
            self.qr_code_data = self.generate_qr_data()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.reg_number} - {self.receipt_number}"
    

# Add this new model for audit logging
class ReceiptPrintLog(models.Model):
    """Track all receipt printing for security audit"""
    receipt = models.ForeignKey(DepartmentalDues, on_delete=models.CASCADE, related_name='print_logs')
    printed_by_student = models.ForeignKey(Student, on_delete=models.CASCADE)
    printed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-printed_at']
        verbose_name_plural = "Receipt Print Logs"
    
    def __str__(self):
        return f"{self.receipt.receipt_number} printed by {self.printed_by_student.reg_number} at {self.printed_at}"


# Add this model for online verification
class ReceiptVerification(models.Model):
    """Track verification attempts"""
    receipt = models.ForeignKey(DepartmentalDues, on_delete=models.CASCADE, related_name='verifications', null=True, blank=True)
    verification_code = models.CharField(max_length=100)
    is_valid = models.BooleanField(default=False)
    verified_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-verified_at']
    
    def __str__(self):
        status = "Valid" if self.is_valid else "Invalid"
        return f"{self.verification_code} - {status}"

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

    
# ==================== RESEARCH MODELS ====================

class ResearchClubRegistration(models.Model):
    """Student registration for research club with manual payment"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, 
                                   related_name='research_club_registration')
    
    # Payment details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    payment_reference = models.CharField(max_length=100, unique=True, blank=True)
    
    # Payment proof
    payment_proof = CloudinaryField('image', blank=True, null=True, 
                                   help_text="Screenshot of bank transfer")
    transaction_description = models.CharField(max_length=200, blank=True,
                                              help_text="Description used in bank transfer")
    payment_date = models.DateField(null=True, blank=True,
                                   help_text="Date of payment as shown on receipt")
    
    # Verification status
    PAYMENT_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, 
                                     default='pending')
    
    # Admin approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   blank=True, related_name='approved_research_registrations')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registered_at']
        verbose_name_plural = "Research Club Registrations"
    
    def __str__(self):
        return f"{self.student.reg_number} - ₦{self.amount_paid} ({self.payment_status})"
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            # Generate unique reference: RC-YEAR-NUMBER
            import datetime
            year = datetime.datetime.now().year
            last = ResearchClubRegistration.objects.filter(
                payment_reference__startswith=f'RC-{year}-'
            ).order_by('-payment_reference').first()
            
            if last:
                last_num = int(last.payment_reference.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.payment_reference = f'RC-{year}-{new_num:04d}'
        
        super().save(*args, **kwargs)


class ResearchTeam(models.Model):
    """Research teams with defined roles"""
    TEAM_ROLES = [
        ('Researchers', 'Researchers'),
        ('Writers', 'Writers'),
        ('Proofreaders', 'Proofreaders'),
        ('Graphic Designers', 'Graphic Designers'),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Team Alpha, Team Beta")
    description = models.TextField()
    focus_area = models.CharField(max_length=200, help_text="e.g., Medical Imaging, Biomechanics")
    team_lead = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='led_teams', help_text="Director of Research assigns team lead")
    image = CloudinaryField('image', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    max_members = models.IntegerField(default=15, help_text="Maximum 15 members per team")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Research Teams"
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        return self.members.count()
    
    def get_contribution_count(self):
        return ResearchContribution.objects.filter(article__team=self).filter(is_approved=True).count()


class ResearchArticle(models.Model):
    """Research articles with collaborative sections"""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('In Progress', 'In Progress'),
        ('Under Review', 'Under Review'),
        ('Published', 'Published'),
    ]
    
    team = models.ForeignKey(ResearchTeam, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=300)
    abstract = models.TextField(help_text="Introduction/Brief overview created by Director")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text="Director of Research")
    published_date = models.DateTimeField(null=True, blank=True)
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Research Articles"
    
    def __str__(self):
        return f"{self.team.name} - {self.title}"
    
    def get_approved_contributions(self):
        """Get contributions ordered by section order"""
        return self.contributions.filter(is_approved=True).order_by('section_order')
    
    def get_total_contributors(self):
        """Count unique contributors (both students and guests)"""
        approved_contributions = self.contributions.filter(is_approved=True)
        
        student_contributors = approved_contributions.filter(
            student_contributor__isnull=False
        ).values_list('student_contributor', flat=True).distinct().count()
        
        guest_contributors = approved_contributions.filter(
            guest_contributor__isnull=False
        ).values_list('guest_contributor', flat=True).distinct().count()
        
        return student_contributors + guest_contributors
    
class GuestContributor(models.Model):
    """External contributors who need approval - Pay ₦2000"""
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    institution = models.CharField(max_length=200, help_text="University/Organization")
    qualification = models.CharField(max_length=200, help_text="e.g., B.Eng, M.Sc, Ph.D")
    area_of_expertise = models.CharField(max_length=200)
    reason_for_contribution = models.TextField()
    password = models.CharField(max_length=128)
    
    # Payment for guest access (₦2000)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)
    payment_reference = models.CharField(max_length=100, unique=True, blank=True)

        # Payment proof
    payment_proof = CloudinaryField('image', blank=True, null=True,
                                   help_text="Screenshot of bank transfer")
    transaction_description = models.CharField(max_length=200, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    
    # Payment status
    PAYMENT_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS,
                                     default='pending')
    
    # Approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approved_guests')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Guest Contributors"
    
    def __str__(self):
        return f"{self.full_name} - {'Approved' if self.is_approved else 'Pending'}"
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"GUEST-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

class ResearchContribution(models.Model):
    """Article sections contributed by team members or guests"""
    SECTION_TYPES = [
        ('Introduction', 'Introduction'),
        ('Background/Definition', 'Background/Definition'),
        ('Main Body', 'Main Body'),
        ('Connection/Integration', 'Connection/Integration'),
        ('Conclusion', 'Conclusion'),
    ]
    
    article = models.ForeignKey(ResearchArticle, on_delete=models.CASCADE, related_name='contributions')
    
    # Contributor (student team member or guest)
    student_contributor = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, 
                                           related_name='research_contributions')
    guest_contributor = models.ForeignKey(GuestContributor, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='research_contributions')
    
    section_title = models.CharField(max_length=300, choices=SECTION_TYPES)
    content = models.TextField()
    references = models.TextField(blank=True, null=True, help_text="Optional citations")
    section_order = models.IntegerField(default=0, help_text="Display order assigned by proofreader")
    
    # Approval workflow
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approved_contributions',
                                    help_text="Proofreader who approved")
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['section_order', 'created_at']
        verbose_name_plural = "Research Contributions"
    
    def __str__(self):
        contributor_name = self.get_contributor_name()
        return f"{contributor_name} - {self.section_title}"
    
    def get_contributor_name(self):
        if self.student_contributor:
            return self.student_contributor.full_name
        elif self.guest_contributor:
            return self.guest_contributor.full_name
        return "Unknown"
    
    def get_contributor_info(self):
        """Detailed contributor info for display"""
        if self.student_contributor:
            return {
                'name': self.student_contributor.full_name,
                'type': 'Student',
                'reg_number': self.student_contributor.reg_number,
                'level': self.student_contributor.get_level_display()
            }
        elif self.guest_contributor:
            return {
                'name': self.guest_contributor.full_name,
                'type': 'Guest',
                'institution': self.guest_contributor.institution,
                'qualification': self.guest_contributor.qualification
            }
        return None
    
class ResearchQuiz(models.Model):
    """Quizzes posted by Director to test knowledge"""
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
        ('Expert', 'Expert'),
    ]
    
    title = models.CharField(max_length=300)
    question = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Medium')
    category = models.CharField(max_length=100, help_text="e.g., Biomechanics, Signal Processing")
    hints = models.TextField(blank=True, null=True)
    points = models.IntegerField(default=10)
    deadline = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Research Quizzes"
    
    def __str__(self):
        return self.title
    
    def get_submissions_count(self):
        return self.submissions.count()
    
    def get_awarded_submissions(self):
        return self.submissions.filter(is_awarded=True).count()


class QuizSubmission(models.Model):
    """Student/Guest submissions for quizzes"""
    quiz = models.ForeignKey(ResearchQuiz, on_delete=models.CASCADE, related_name='submissions')
    
    # Submitter
    student_submitter = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='quiz_submissions')
    guest_submitter = models.ForeignKey(GuestContributor, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='quiz_submissions')
    
    answer = models.TextField()
    explanation = models.TextField(help_text="Detailed step-by-step explanation")
    attachments = CloudinaryField('file', blank=True, null=True)
    
    # Award status
    is_awarded = models.BooleanField(default=False)
    award_comment = models.TextField(blank=True, null=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='awarded_quizzes')
    awarded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Quiz Submissions"
        unique_together = [
            ['quiz', 'student_submitter'],
            ['quiz', 'guest_submitter']
        ]
    
    def __str__(self):
        submitter = self.get_submitter_name()
        return f"{submitter} - {self.quiz.title}"
    
    def get_submitter_name(self):
        if self.student_submitter:
            return self.student_submitter.full_name
        elif self.guest_submitter:
            return self.guest_submitter.full_name
        return "Unknown"
    
    def get_submitter_info(self):
        if self.student_submitter:
            return {
                'name': self.student_submitter.full_name,
                'type': 'Student',
                'reg_number': self.student_submitter.reg_number
            }
        elif self.guest_submitter:
            return {
                'name': self.guest_submitter.full_name,
                'type': 'Guest',
                'institution': self.guest_submitter.institution
            }
        return None


class TeamMembership(models.Model):
    """Track team members with specific roles"""
    ROLE_CHOICES = [
        ('Researcher', 'Researcher'),
        ('Writer', 'Writer'),
        ('Proofreader', 'Proofreader'),
        ('Graphic Designer', 'Graphic Designer'),
    ]
    
    team = models.ForeignKey(ResearchTeam, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='research_teams')
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='Researcher')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['team', 'student']
        ordering = ['-joined_at']
        verbose_name_plural = "Team Memberships"
    
    def __str__(self):
        return f"{self.student.full_name} - {self.team.name} ({self.role})"

class ArticleLike(models.Model):
    """Track article likes from students only"""
    article = models.ForeignKey(ResearchArticle, on_delete=models.CASCADE, related_name='likes')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='liked_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['article', 'student']
        verbose_name_plural = "Article Likes"
    
    def __str__(self):
        return f"{self.student.full_name} liked {self.article.title}"
    


class ArticleComment(models.Model):
    """Comments on published articles"""
    article = models.ForeignKey(ResearchArticle, on_delete=models.CASCADE, related_name='comments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='article_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Article Comments"
    
    def __str__(self):
        return f"{self.student.full_name} on {self.article.title}"



# Add to existing models.py

class AccessPin(models.Model):
    """One-time use access pins for portal registration"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    
    pin = models.CharField(max_length=20, unique=True, primary_key=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_pins')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Usage tracking
    used_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_pin')
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiry date")
    
    # Batch tracking
    batch_number = models.CharField(max_length=50, blank=True, help_text="For bulk generation tracking")
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name_plural = "Access Pins"
    
    def __str__(self):
        return f"{self.pin} - {self.status}"
    
    def is_valid(self):
        """Check if pin is valid for use"""
        if self.status != 'active':
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            return False
        
        return True
    
    def mark_as_used(self, student):
        """Mark pin as used by a student"""
        self.status = 'used'
        self.used_by = student
        self.used_at = timezone.now()
        self.save()
    
    @staticmethod
    def generate_pin():
        """Generate a unique 12-character PIN"""
        import random
        import string
        
        while True:
            # Format: BME-XXXX-XXXX where X is alphanumeric
            part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            pin = f"BME-{part1}-{part2}"
            
            # Check if pin already exists
            if not AccessPin.objects.filter(pin=pin).exists():
                return pin


class PinUsageLog(models.Model):
    """Track all PIN usage attempts for security"""
    pin = models.ForeignKey(AccessPin, on_delete=models.CASCADE, related_name='usage_logs')
    student_reg_number = models.CharField(max_length=50, blank=True)
    attempt_successful = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    others = models.CharField(null=True, blank=True)
    
    class Meta:
        ordering = ['-attempted_at']
        verbose_name_plural = "PIN Usage Logs"
    
    def __str__(self):
        status = "Success" if self.attempt_successful else "Failed"
        return f"{self.pin.pin} - {status} - {self.attempted_at}"


# ==================== ADD THIS BLOCK TO THE BOTTOM OF models.py ====================

class IDCardApplication(models.Model):
    """Students apply for a physical ID card by uploading their passport photo"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('printed', 'Printed'),
        ('rejected', 'Rejected'),
    ]

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='id_card_application',
    )
    passport_photo = CloudinaryField(
        'image',
        help_text='Upload a clear passport photograph (white background, face visible)',
    )
    academic_session = models.CharField(
        max_length=20,
        help_text='e.g., 2024/2025',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    # Admin fields
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_id_applications',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        verbose_name = 'ID Card Application'
        verbose_name_plural = 'ID Card Applications'

    def __str__(self):
        return f'{self.student.reg_number} – {self.status}'