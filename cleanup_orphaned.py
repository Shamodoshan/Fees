import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import DraftPayment, StudentMonthlyStatus

print("Cleaning up orphaned payments:")
print("=" * 40)

# Find and remove payments without students
orphaned_payments = DraftPayment.objects.filter(student__isnull=True)
print(f"Found {orphaned_payments.count()} orphaned payments")

for payment in orphaned_payments:
    print(f"  Removing: {payment.amount} - {payment.status} - {payment.month}/{payment.year}")
    payment.delete()

print("\nAfter cleanup:")
remaining_orphaned = DraftPayment.objects.filter(student__isnull=True).count()
print(f"Remaining orphaned payments: {remaining_orphaned}")

# Check current StudentMonthlyStatus
print("\nCurrent StudentMonthlyStatus records:")
for status in StudentMonthlyStatus.objects.all():
    print(f"  {status.student.name} - {status.year}/{status.month}: {status.status} - Rs.{status.paid_amount}")
