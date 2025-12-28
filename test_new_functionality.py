import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Student, DraftPayment
from decimal import Decimal

def test_new_functionality():
    print("Testing new Student model functionality...")
    
    # Test 1: Check if monthly_payments field exists
    students = Student.objects.all()
    print(f"Found {students.count()} students")
    
    for student in students:
        print(f"\nStudent: {student.name}")
        print(f"Monthly fee: Rs.{student.monthly_fee}")
        print(f"Monthly payments data: {student.monthly_payments}")
        
        # Test get_monthly_status
        if student.monthly_payments:
            first_month_key = list(student.monthly_payments.keys())[0]
            year, month = map(int, first_month_key.split('-'))
            status = student.get_monthly_status(year, month)
            print(f"Status for {year}/{month}: {status}")
        
        # Test get_last_paid_month
        last_paid = student.get_last_paid_month()
        if last_paid:
            print(f"Last paid: {last_paid[0]}/{last_paid[1]} - {last_paid[2].get('status')}")
        else:
            print("No payment history")
    
    # Test 2: Test get_unpaid_students_for_month
    print("\n\nTesting unpaid students for December 2025:")
    unpaid = Student.get_unpaid_students_for_month(2025, 12)
    print(f"Unpaid students: {unpaid.count()}")
    for student in unpaid:
        print(f"  - {student.name}")
    
    # Test 3: Test monthly report
    print("\n\nTesting monthly report for December 2025:")
    report = Student.get_monthly_report(2025, 12)
    print(f"Report: {report}")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_new_functionality()
