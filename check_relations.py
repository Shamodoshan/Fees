import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import DraftPayment, StudentMonthlyStatus, Student
from decimal import Decimal

print("Checking database relations and half payments:")
print("=" * 60)

# Check for payments without students
print("\nPayments without students:")
payments_without_student = DraftPayment.objects.filter(student__isnull=True)
for payment in payments_without_student:
    print(f"  Payment ID {payment.id}: Rs.{payment.amount} - {payment.status} - {payment.month}/{payment.year}")

# Check StudentMonthlyStatus records
print("\nStudentMonthlyStatus records:")
for status in StudentMonthlyStatus.objects.all():
    print(f"  {status.student.name if status.student else 'No Student'} - {status.year}/{status.month}: {status.status} - Rs.{status.paid_amount}")

# Check if there's a relation issue
print("\nChecking for orphaned StudentMonthlyStatus:")
orphaned_statuses = StudentMonthlyStatus.objects.filter(student__isnull=True)
print(f"  Found {orphaned_statuses.count()} orphaned status records")

# Check students and their monthly fees
print("\nStudents and monthly fees:")
for student in Student.objects.all():
    print(f"  {student.name}: Rs.{student.monthly_fee}")
