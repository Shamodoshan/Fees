import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import DraftPayment

print("Checking DraftPayment records:")
print("=" * 50)

payments = DraftPayment.objects.all().order_by('-created_date')
for payment in payments:
    print(f"Student: {payment.student.name if payment.student else 'Unknown'}")
    print(f"  Amount: Rs.{payment.amount}")
    print(f"  Status: {payment.status}")
    print(f"  Month/Year: {payment.month}/{payment.year}")
    print(f"  Created: {payment.created_date}")
    print("-" * 30)
