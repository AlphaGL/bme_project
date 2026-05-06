from django import forms
from .models import *


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'position', 'bio', 'email', 'phone', 'image', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ExcoForm(forms.ModelForm):
    class Meta:
        model = Exco
        fields = ['name', 'position', 'bio', 'email', 'phone', 'image', 'session', 'order', 'is_msrc']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'session': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2023/2024'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_msrc': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'is_msrc': 'Check this box if this person is a Member of Student Representative Council'
        }

class PastQuestionForm(forms.ModelForm):
    class Meta:
        model = PastQuestion
        fields = ['course_code', 'course_title', 'level', 'semester', 'year', 'link', 'description']
        widgets = {
            'course_code': forms.TextInput(attrs={'class': 'form-control'}),
            'course_title': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class LibraryResourceForm(forms.ModelForm):
    class Meta:
        model = LibraryResource
        fields = ['title', 'author', 'category', 'description', 'link', 'cover_image', 'level']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
        }

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'message', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# NEW STUDENT FORMS
class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'id': 'id_password'
        }),
        help_text='Create a secure password (minimum 6 characters recommended)'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'id_confirm_password'
        })
    )
    confirm_reg_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Registration Number'
        })
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I agree to pay ₦1,250 for portal access (one-time payment)'
    )

    class Meta:
        model = Student
        fields = ['reg_number', 'full_name', 'email', 'phone']
        widgets = {
            'reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 202XXXXXXXX'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
        }

    def clean_reg_number(self):
        reg_number = self.cleaned_data.get('reg_number')
        
        # Check if reg number exists in RegisteredRegNumber
        from core.models import RegisteredRegNumber
        if not RegisteredRegNumber.objects.filter(reg_number=reg_number, is_active=True).exists():
            raise forms.ValidationError(
                "This registration number is not registered in our system. "
                "If you are a BME student, please contact the admin to add your registration number."
            )
        
        # Check if already registered
        if Student.objects.filter(reg_number=reg_number).exists():
            raise forms.ValidationError(
                "This registration number is already registered. Please login instead."
            )
        
        return reg_number

    def clean(self):
        cleaned_data = super().clean()
        reg_number = cleaned_data.get('reg_number')
        confirm_reg_number = cleaned_data.get('confirm_reg_number')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if reg_number and confirm_reg_number:
            if reg_number != confirm_reg_number:
                raise forms.ValidationError("Registration numbers do not match!")
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
            if len(password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters long!")
        
        return cleaned_data
    
    def save(self, commit=True):
        student = super().save(commit=False)
        student.set_password(self.cleaned_data['password'])
        
        # Get level from RegisteredRegNumber
        from core.models import RegisteredRegNumber
        try:
            reg_entry = RegisteredRegNumber.objects.get(reg_number=student.reg_number)
            student.level = reg_entry.level
        except RegisteredRegNumber.DoesNotExist:
            pass
        
        if commit:
            student.save()
        return student 


# ==================== RESEARCH CLUB REGISTRATION FORMS ====================

class ResearchClubRegistrationForm(forms.ModelForm):
    """Student registers for research club"""
    payment_proof = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload screenshot of your bank transfer'
    )
    
    transaction_description = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What description did you use? (e.g., your reg number)'
        })
    )
    
    payment_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Date shown on your payment receipt'
    )
    
    confirm_payment = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that I have transferred ₦1,000 to the account provided'
    )
    
    class Meta:
        model = ResearchClubRegistration
        fields = ['payment_proof', 'transaction_description', 'payment_date']


class GuestContributorRegistrationForm(forms.ModelForm):
    """Updated guest registration form with ₦2000 manual payment"""
    
    # Password fields
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        }),
        help_text='Choose a strong password for future login'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Payment proof fields
    payment_proof = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload screenshot of your ₦2,000 bank transfer'
    )
    
    transaction_description = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What description did you use? (e.g., your email or name)'
        }),
        help_text='The description/narration you used in the bank transfer'
    )
    
    payment_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Date shown on your payment receipt'
    )
    
    # Terms acceptance
    confirm_payment = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that I have transferred ₦2,000 to the account provided'
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I agree to the terms and conditions of guest contribution'
    )
    
    class Meta:
        model = GuestContributor
        fields = ['full_name', 'email', 'phone', 'institution', 'qualification', 
                  'area_of_expertise', 'reason_for_contribution',
                  'payment_proof', 'transaction_description', 'payment_date']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your university or organization'
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., B.Eng, M.Sc, Ph.D'
            }),
            'area_of_expertise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Biomedical Signal Processing'
            }),
            'reason_for_contribution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Why do you want to contribute to our research?'
            }),
        }
    
    def clean_email(self):
        """Check if email already exists"""
        email = self.cleaned_data.get('email')
        if GuestContributor.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered. Please login instead."
            )
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Validate passwords match
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
            if len(password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters long!")
        
        return cleaned_data
    
    def save(self, commit=True):
        guest = super().save(commit=False)
        
        # Set password
        guest.set_password(self.cleaned_data['password'])
        
        # Set payment status to pending
        guest.payment_status = 'pending'
        guest.is_approved = False
        
        if commit:
            guest.save()
        return guest
    
class RegistrationRequestForm(forms.ModelForm):
    """Form for students not in the system to request registration"""
    
    class Meta:
        model = RegistrationRequest
        fields = ['reg_number', 'full_name', 'email', 'phone', 'level', 'reason', 'proof_document']
        widgets = {
            'reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024/1/12345'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain why you should be added to the system (e.g., newly admitted student, transferred from another department, etc.)'
            }),
        }
    
    def clean_reg_number(self):
        reg_number = self.cleaned_data.get('reg_number')
        
        # Check if already registered
        if Student.objects.filter(reg_number=reg_number).exists():
            raise forms.ValidationError(
                "This registration number is already registered. Please login instead."
            )
        
        # Check if request already exists
        if RegistrationRequest.objects.filter(
            reg_number=reg_number, 
            status='pending'
        ).exists():
            raise forms.ValidationError(
                "You have already submitted a registration request. Please wait for admin approval."
            )
        
        return reg_number
    
class StudentLoginForm(forms.Form):
    reg_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registration number',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'id_login_password'
        })
    )


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password',
            'id': 'id_current_password'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'id': 'id_new_password'
        }),
        help_text='Minimum 6 characters recommended'
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'id': 'id_confirm_new_password'
        })
    )
    
    def __init__(self, student, *args, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.student.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect!")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')
        
        if new_password and confirm_new_password:
            if new_password != confirm_new_password:
                raise forms.ValidationError("New passwords do not match!")
            if len(new_password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters long!")
        
        return cleaned_data

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'email', 'phone', 'level', 'profile_image']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234XXXXXXXXXX'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'year']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100 Level First Semester'
            }),
            'year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2023/2024 (optional)'
            }),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'course_name', 'credit_unit', 'grade_point']
        widgets = {
            'course_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BME 101'
            }),
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Introduction to Biomedical Engineering'
            }),
            'credit_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 6
            }),
            'grade_point': forms.Select(attrs={'class': 'form-control'}),
        }


class DepartmentalDuesForm(forms.ModelForm):
    class Meta:
        model = DepartmentalDues
        fields = ['student', 'amount_paid', 'academic_session', 'is_approved']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '10000.00'
            }),
            'academic_session': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2025/2026'
            }),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseHandbookForm(forms.ModelForm):
    class Meta:
        model = CourseHandbook
        fields = ['level', 'semester', 'course_code', 'course_title', 'credit_unit', 'course_type', 'description']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'course_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BME 101'
            }),
            'course_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Introduction to Biomedical Engineering'
            }),
            'credit_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 6
            }),
            'course_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional course description'
            }),
        }


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['title', 'timetable_type', 'level', 'semester', 'academic_session', 'image', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., First Semester Examination Timetable 2023/2024'
            }),
            'timetable_type': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'academic_session': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2023/2024'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AcademicCalendarForm(forms.ModelForm):
    class Meta:
        model = AcademicCalendar
        fields = ['title', 'academic_session', 'image', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Academic Calendar 2023/2024'
            }),
            'academic_session': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2023/2024'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# ==================== RESEARCH FORMS ====================

class ResearchTeamForm(forms.ModelForm):
    class Meta:
        model = ResearchTeam
        fields = ['name', 'description', 'focus_area', 'team_lead', 'image', 'is_active', 'max_members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Team Alpha'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the team focus and objectives'
            }),
            'focus_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Medical Imaging, Biomechanics'
            }),
            'team_lead': forms.Select(attrs={'class': 'form-control'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResearchArticleForm(forms.ModelForm):
    class Meta:
        model = ResearchArticle
        fields = ['team', 'title', 'abstract', 'status']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Research article title'
            }),
            'abstract': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Brief overview of the research'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class GuestContributorForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        }),
        help_text='Choose a strong password for future contributions'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    class Meta:
        model = GuestContributor
        fields = ['full_name', 'email', 'phone', 'institution', 'qualification', 
                  'area_of_expertise', 'reason_for_contribution']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your university or organization'
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., B.Eng, M.Sc, Ph.D'
            }),
            'area_of_expertise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Biomedical Signal Processing'
            }),
            'reason_for_contribution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Why do you want to contribute to our research?'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data
    
    def save(self, commit=True):
        guest = super().save(commit=False)
        guest.set_password(self.cleaned_data['password'])
        if commit:
            guest.save()
        return guest


class GuestLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )


class ResearchContributionForm(forms.ModelForm):
    """Enhanced contribution form with section types"""
    class Meta:
        model = ResearchContribution
        fields = ['section_title', 'content', 'references']
        widgets = {
            'section_title': forms.Select(attrs={
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Write your contribution here... Be detailed and well-researched.'
            }),
            'references': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'List your references (optional)'
            }),
        }

class ResearchQuizForm(forms.ModelForm):
    class Meta:
        model = ResearchQuiz
        fields = ['title', 'question', 'difficulty_level', 'category', 'hints', 'points', 'deadline', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quiz title'
            }),
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter the quiz question'
            }),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Biomechanics'
            }),
            'hints': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional hints for participants'
            }),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuizSubmissionForm(forms.ModelForm):
    class Meta:
        model = QuizSubmission
        fields = ['answer', 'explanation', 'attachments']
        widgets = {
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Your answer to the quiz'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Explain your solution process in detail'
            }),
        }


class TeamJoinForm(forms.ModelForm):
    """Form for students to join a team with role selection"""
    class Meta:
        model = TeamMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        help_texts = {
            'role': 'Select your role in the team'
        }


class ApproveContributionForm(forms.Form):
    """Form for proofreaders to approve contributions with section ordering"""
    section_order = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter section order (1, 2, 3...)'
        }),
        help_text='Order in which this section should appear in the article'
    )


class ArticleCommentForm(forms.ModelForm):
    """Form for students to comment on articles"""
    class Meta:
        model = ArticleComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...'
            })
        }


class PinRegistrationForm(forms.ModelForm):
    """Registration form using PIN"""
    access_pin = forms.CharField(
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'BME-XXXX-XXXX',
            'style': 'text-transform: uppercase;'
        }),
        help_text='Enter the 12-character access PIN you purchased from the department'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        }),
        help_text='Create a secure password (minimum 6 characters)'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    confirm_reg_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Registration Number'
        })
    )
    
    class Meta:
        model = Student
        fields = ['reg_number', 'full_name', 'email', 'phone']
        widgets = {
            'reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 202X1234567'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
        }
    
    def clean_access_pin(self):
        pin = self.cleaned_data.get('access_pin', '').strip().upper()
        
        try:
            access_pin = AccessPin.objects.get(pin=pin)
            
            if not access_pin.is_valid():
                if access_pin.status == 'used':
                    raise forms.ValidationError(
                        f"This PIN has already been used by another student on "
                        f"{access_pin.used_at.strftime('%B %d, %Y')}."
                    )
                elif access_pin.status == 'expired':
                    raise forms.ValidationError("This PIN has expired. Please contact the department.")
                else:
                    raise forms.ValidationError("This PIN is not valid.")
            
            self.access_pin_obj = access_pin
            
        except AccessPin.DoesNotExist:
            raise forms.ValidationError(
                "Invalid PIN. Please check and try again. "
                "Format should be BME-XXXX-XXXX"
            )
        
        return pin
    
    def clean_reg_number(self):
        reg_number = self.cleaned_data.get('reg_number')
        
        # Check if already registered
        if Student.objects.filter(reg_number=reg_number).exists():
            raise forms.ValidationError(
                "This registration number is already registered. Please login instead."
            )
        
        # Check if in registered numbers
        from core.models import RegisteredRegNumber
        if not RegisteredRegNumber.objects.filter(reg_number=reg_number, is_active=True).exists():
            raise forms.ValidationError(
                "This registration number is not in our system. "
                "Please contact the department or submit a registration request."
            )
        
        return reg_number
    
    def clean(self):
        cleaned_data = super().clean()
        reg_number = cleaned_data.get('reg_number')
        confirm_reg_number = cleaned_data.get('confirm_reg_number')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if reg_number and confirm_reg_number:
            if reg_number != confirm_reg_number:
                raise forms.ValidationError("Registration numbers do not match!")
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
            if len(password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters long!")
        
        return cleaned_data
    
    def save(self, commit=True):
        student = super().save(commit=False)
        student.set_password(self.cleaned_data['password'])
        student.payment_method = 'pin'
        student.has_paid = True
        student.payment_verified_at = timezone.now()
        student.access_pin_used = self.access_pin_obj
        
        # Get level from RegisteredRegNumber
        from core.models import RegisteredRegNumber
        try:
            reg_entry = RegisteredRegNumber.objects.get(reg_number=student.reg_number)
            student.level = reg_entry.level
        except RegisteredRegNumber.DoesNotExist:
            pass
        
        if commit:
            student.save()
            # Mark PIN as used
            self.access_pin_obj.mark_as_used(student)
        
        return student


class GeneratePinForm(forms.Form):
    """Form for admin to generate PINs"""
    quantity = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of PINs to generate'
        }),
        help_text='Generate between 1 and 100 PINs at once'
    )
    
    batch_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Batch 2025-01 (optional)'
        }),
        help_text='Optional: Name this batch for tracking'
    )
    
    expires_in_days = forms.IntegerField(
        min_value=0,
        max_value=365,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Days until expiry (leave blank for no expiry)'
        }),
        help_text='Optional: Number of days until PINs expire (0 or blank = never)'
    )


class PinAccessVerifyForm(forms.Form):
    """Form to verify PIN access password"""
    access_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter PIN management password',
            'autofocus': True
        }),
        help_text='Enter the special password to access PIN management'
    )
    
    def clean_access_password(self):
        password = self.cleaned_data.get('access_password')
        
        # The special password
        SPECIAL_PASSWORD = 'Ibeawuchicn@242'
        
        if password != SPECIAL_PASSWORD:
            raise forms.ValidationError('Incorrect password. Access denied.')
        
        return password


class IDCardApplicationForm(forms.ModelForm):
    class Meta:
        model = IDCardApplication
        fields = ['passport_photo', 'academic_session']
        widgets = {
            'academic_session': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024/2025',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['passport_photo'].widget.attrs.update({'class': 'form-control'})
        self.fields['academic_session'].label = 'Academic Session'
        self.fields['passport_photo'].label = 'Passport Photograph'
        self.fields['passport_photo'].help_text = (
            'Upload a ID CARD IMAGE. '
            'Your face must be clearly visible. Max size: 2 MB.'
        )



# ==================== FORGOT PASSWORD ====================

class ForgotPasswordForm(forms.Form):
    """Step 1: Verify student identity before allowing password reset"""
    reg_number = forms.CharField(
        max_length=50,
        label='Registration Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 202X1234567',
            'autofocus': True
        })
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the email used during registration'
        })
    )
    phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the phone number used during registration'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        reg_number = cleaned_data.get('reg_number')
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')

        if reg_number and email and phone:
            try:
                from .models import Student
                student = Student.objects.get(reg_number=reg_number)

                # Verify email matches (case-insensitive)
                if student.email and student.email.lower() != email.lower():
                    raise forms.ValidationError(
                        'The details you provided do not match our records. '
                        'Please check your registration number, email, and phone number.'
                    )

                # Verify phone matches.
                # Normalise both numbers to their last 10 digits so that
                # 2348138582078, 08138582078, and 8138582078 all compare equal.
                def normalise_phone(p):
                    digits = ''.join(filter(str.isdigit, p or ''))
                    # Strip country code prefixes
                    if digits.startswith('234'):
                        digits = digits[3:]   # 234XXXXXXXXXX → XXXXXXXXXX
                    if digits.startswith('0'):
                        digits = digits[1:]   # 0XXXXXXXXXX  → XXXXXXXXXX
                    return digits  # last 10 digits (e.g. 8138582078)

                if student.phone and normalise_phone(student.phone) != normalise_phone(phone):
                    raise forms.ValidationError(
                        'The details you provided do not match our records. '
                        'Please check your registration number, email, and phone number.'
                    )

                # All good – attach student so the view can use it
                self.verified_student = student

            except Student.DoesNotExist:
                raise forms.ValidationError(
                    'No account found with that registration number.'
                )

        return cleaned_data


class ResetPasswordForm(forms.Form):
    """Step 2: Set a new password after identity has been verified"""
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'id': 'id_reset_new_password'
        }),
        help_text='Minimum 6 characters'
    )
    confirm_new_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter new password',
            'id': 'id_reset_confirm_password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_new_password')

        if new_password and confirm:
            if new_password != confirm:
                raise forms.ValidationError('Passwords do not match!')
            if len(new_password) < 6:
                raise forms.ValidationError('Password must be at least 6 characters long!')

        return cleaned_data