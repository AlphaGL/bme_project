from django import template
from core.models import Student

register = template.Library()

@register.filter
def is_student_registered(reg_number):
    """Check if a student with this reg_number has already created an account"""
    return Student.objects.filter(reg_number=reg_number).exists()


@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0