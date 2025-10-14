from django import forms
from .models import( Staff, Exco, PastQuestion, LibraryResource,
                     Testimonial, Announcement, Student, Semester, Course, 
                     DepartmentalDues, CourseHandbook, Timetable, AcademicCalendar
                    )

# ADD THESE FORMS

# Existing forms...
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
        fields = ['name', 'position', 'bio', 'email', 'phone', 'image', 'session', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'session': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2023/2024'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
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
    confirm_reg_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Registration Number'
        })
    )

    class Meta:
        model = Student
        fields = ['reg_number', 'full_name', 'email', 'level']
        widgets = {
            'reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2020/1/12345'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com (optional)'
            }),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        reg_number = cleaned_data.get('reg_number')
        confirm_reg_number = cleaned_data.get('confirm_reg_number')

        if reg_number and confirm_reg_number:
            if reg_number != confirm_reg_number:
                raise forms.ValidationError("Registration numbers do not match!")
        
        return cleaned_data


class StudentLoginForm(forms.Form):
    reg_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registration number',
            'autofocus': True
        })
    )


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
                'placeholder': '5000.00'
            }),
            'academic_session': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2023/2024'
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