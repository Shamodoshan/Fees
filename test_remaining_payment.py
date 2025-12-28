import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import Student, DraftPayment, StudentMonthlyStatus
from decimal import Decimal

# Get the student with half payment
student = Student.objects.first()
print(f"Testing remaining payment for student: {student.name}")
print(f"Monthly fee: Rs.{student.monthly_fee}")

# Check current status
current_status = StudentMonthlyStatus.objects.filter(student=student, month=12, year=2025).first()
if current_status:
    print(f"Current status: {current_status.status} - Rs.{current_status.paid_amount}")
    
    # Calculate remaining amount
    remaining = student.monthly_fee - current_status.paid_amount
    print(f"Remaining amount: Rs.{remaining}")
    
    # Create remaining payment
    if remaining > 0:
        payment = DraftPayment.objects.create(
            student=student,
            amount=remaining,
            monthly_fee=student.monthly_fee,
            description="Remaining payment test",
            month=12,
            year=2025,
            status='Paid'  # This should become 'Paid' after processing
        )
        print(f"Created remaining payment: {payment}")
        
        # Update StudentMonthlyStatus (simulating the add_payment logic)
        total_paid = current_status.paid_amount + remaining
        if total_paid >= student.monthly_fee:
            new_status = 'Paid'
            paid_amount = student.monthly_fee
        else:
            new_status = 'Half Paid'
            paid_amount = total_paid
            
        current_status.paid_amount = paid_amount
        current_status.status = new_status
        current_status.save()
        
        print(f"Updated status: {current_status.status} - Rs.{current_status.paid_amount}")
    else:
        print("No remaining amount needed")
else:
    print("No current status found")
