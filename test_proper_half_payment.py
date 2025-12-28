import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import Student, DraftPayment, StudentMonthlyStatus
from decimal import Decimal

# Get a student for testing
student = Student.objects.first()
print(f"Creating proper half payment for student: {student.name}")
print(f"Monthly fee: Rs.{student.monthly_fee}")

# Create a proper half payment with student link
half_amount = student.monthly_fee / Decimal('2')
print(f"Half payment amount: Rs.{half_amount}")

# Create DraftPayment with student link
payment = DraftPayment.objects.create(
    student=student,
    amount=half_amount,
    monthly_fee=student.monthly_fee,
    description="Proper half payment test",
    month=11,  # November (should be unpaid)
    year=2025,
    status='Half Paid'
)

print(f"Created payment: {payment}")

# Create or update StudentMonthlyStatus
monthly_status, created = StudentMonthlyStatus.objects.get_or_create(
    student=student,
    month=11,
    year=2025,
    defaults={'paid_amount': Decimal('0'), 'status': 'Unpaid'}
)

# Update with half payment
monthly_status.paid_amount = half_amount
monthly_status.status = 'Half Paid'
monthly_status.save()

print(f"StudentMonthlyStatus: {monthly_status.status} - Rs.{monthly_status.paid_amount}")

# Now test the annual report logic
print(f"\nTesting annual report for {student.name} in 2025:")
from core.views import student_annual_report
from django.test import RequestFactory
from django.contrib.auth.models import User

# Create a mock request
factory = RequestFactory()
user = User.objects.first()
request = factory.get(f'/student-annual-report/?student_id={student.id}&year=2025')
request.user = user

# Call the view function
response = student_annual_report(request)
print(f"Annual report response status: {response.status_code}")

# Check the context data
if hasattr(response, 'context_data'):
    months = response.context_data.get('months', [])
    for month_data in months:
        if month_data['month'] == 11:
            print(f"November: {month_data['status']} - Rs.{month_data['paid_amount']}")
            break
