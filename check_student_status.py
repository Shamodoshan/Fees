import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import StudentMonthlyStatus, Student

print("Checking StudentMonthlyStatus records:")
print("=" * 50)

# Get all students
students = Student.objects.all()
for student in students:
    print(f"\nStudent: {student.name}")
    statuses = StudentMonthlyStatus.objects.filter(student=student).order_by('-year', '-month')
    for status in statuses:
        print(f"  {status.year}/{status.month}: {status.status} - Rs.{status.paid_amount}")
