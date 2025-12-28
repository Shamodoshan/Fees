import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import Student, DraftPayment, StudentMonthlyStatus
from decimal import Decimal

# Get a student
student = Student.objects.first()
print(f"Creating half payment for student: {student.name}")
print(f"Monthly fee: Rs.{student.monthly_fee}")

# Create a half payment (pay half of monthly fee)
half_amount = student.monthly_fee / Decimal('2')
print(f"Half payment amount: Rs.{half_amount}")

# Create DraftPayment with Half Paid status
payment = DraftPayment.objects.create(
    student=student,
    amount=half_amount,
    monthly_fee=student.monthly_fee,
    description="Half payment test",
    month=12,  # December
    year=2025,
    status='Half Paid'
)

print(f"Created payment: {payment}")

# Create or update StudentMonthlyStatus
monthly_status, created = StudentMonthlyStatus.objects.get_or_create(
    student=student,
    month=12,
    year=2025,
    defaults={'paid_amount': Decimal('0'), 'status': 'Unpaid'}
)

# Update with half payment
monthly_status.paid_amount = half_amount
monthly_status.status = 'Half Paid'
monthly_status.save()

print(f"StudentMonthlyStatus: {monthly_status.status} - Rs.{monthly_status.paid_amount}")
