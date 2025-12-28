
from core.models import Student, HolidayMonth
from core.views import get_next_payment_month_year
from decimal import Decimal
from django.utils import timezone

# Setup
current_year = timezone.now().year
current_month = timezone.now().month

# 1. Basic Half Paid Test
s1 = Student.objects.create(name="Test Half Paid", monthly_fee=1000, 
                          year=current_year, month=current_month, 
                          paid_amount=500, payment_status='Half Paid')

m, y, remaining = get_next_payment_month_year(s1)
print(f"Test 1 (Basic): Paid 500/1000. Remaining expected 500. Got: {remaining}")

# 2. Holiday Half Paid Test
# Create holiday (200 off) for next month
h_month = current_month + 1
h_year = current_year
if h_month > 12:
    h_month = 1
    h_year += 1
    
HolidayMonth.objects.update_or_create(
    year=h_year, month=h_month, 
    defaults={'discount_type': 'Amount', 'discount_value': 200}
)

s2 = Student.objects.create(name="Test Holiday Half Paid", monthly_fee=1000, 
                          year=h_year, month=h_month, 
                          paid_amount=500, payment_status='Half Paid')

m2, y2, remaining2 = get_next_payment_month_year(s2)
# Required: 1000 - 200 = 800. Paid: 500. Remaining: 300.
print(f"Test 2 (Holiday): Paid 500/800. Remaining expected 300. Got: {remaining2}")

# Cleanup
s1.delete()
s2.delete()
HolidayMonth.objects.filter(year=h_year, month=h_month).delete()
