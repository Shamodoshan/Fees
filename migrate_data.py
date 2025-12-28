import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Student, StudentMonthlyStatus
from django.utils import timezone

def migrate_monthly_status_to_student():
    """Migrate all StudentMonthlyStatus records to Student.monthly_payments JSONField"""
    print("Starting data migration...")
    
    students_processed = 0
    records_migrated = 0
    
    # Process all students
    for student in Student.objects.all():
        monthly_data = {}
        
        # Get all monthly status records for this student
        status_records = StudentMonthlyStatus.objects.filter(student=student)
        
        for record in status_records:
            month_key = f"{record.year:04d}-{record.month:02d}"
            monthly_data[month_key] = {
                'status': record.status,
                'amount': float(record.paid_amount),
                'paid_date': None,  # We don't have this info in old model
                'last_updated': timezone.now().isoformat(),
                'monthly_fee': float(student.monthly_fee)  # Add reference
            }
            records_migrated += 1
        
        # Update student with migrated data
        if monthly_data:
            student.monthly_payments = monthly_data
            student.save(update_fields=['monthly_payments'])
            students_processed += 1
            print(f"Migrated {len(monthly_data)} months for student: {student.name}")
    
    print(f"\nMigration complete!")
    print(f"Students processed: {students_processed}")
    print(f"Records migrated: {records_migrated}")
    
    # Verify data
    print("\nVerification:")
    for student in Student.objects.all()[:3]:  # Check first 3 students
        print(f"Student: {student.name}")
        print(f"Monthly payments: {student.monthly_payments}")

if __name__ == "__main__":
    migrate_monthly_status_to_student()
