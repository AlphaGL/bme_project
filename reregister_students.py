import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bmefuto_project.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from core.models import Student  # adjust 'portal' if your app name is different

STUDENTS = [
    {"reg_number": "20241450713", "full_name": "Abika Joy C", "level": "200"},
    {"reg_number": "20241427453", "full_name": "Umunna Miracle Ngozi", "level": "200"},
]

for data in STUDENTS:
    reg = data["reg_number"]
    student, created = Student.objects.update_or_create(
        reg_number=reg,
        defaults={
            "full_name": data["full_name"],
            "level": data["level"],
            "password": make_password(reg),
        }
    )
    action = "Created" if created else "Re-registered"
    print(f"[{action}] {student.full_name} | Reg: {reg} | Level: {data['level']}L")

print("\nDone. Students can now log in with their reg number as password.")