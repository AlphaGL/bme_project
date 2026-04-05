import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bmefuto_project.settings')
django.setup()

from core.models import Student  # adjust 'core' if needed

REG_NUMBERS = [
    "20241452483",
]

for reg in REG_NUMBERS:
    try:
        student = Student.objects.get(reg_number=reg)
        student.has_paid = True
        student.payment_verified_at = timezone.now()
        student.payment_method = "pin"  # mark as manually approved
        student.save()
        print(f"[APPROVED] {student.full_name} | {reg}")
    except Student.DoesNotExist:
        print(f"[NOT FOUND] {reg}")

print("\nDone. Students can now access their dashboard without payment.")