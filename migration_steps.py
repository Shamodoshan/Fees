# MIGRATION STEPS - Safe Data Migration from StudentMonthlyStatus to Student

# Step 1: Create Migration File
# python manage.py makemigrations core --name add_monthly_payments_to_student

"""
Migration 1: Add monthly_payments JSONField to Student model
"""

from django.db import migrations, models
import django.core.serializers.json
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        ('core', 'current_last_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='monthly_payments',
            field=models.JSONField(
                default=dict,
                encoder=django.core.serializers.json.DjangoJSONEncoder,
                help_text='Monthly payment status and amounts in JSON format'
            ),
        ),
        # Add GIN index for PostgreSQL
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_monthly_payments_gin ON core_student USING GIN (monthly_payments);",
            reverse_sql="DROP INDEX IF EXISTS idx_student_monthly_payments_gin;"
        ),
    ]

# Step 2: Data Migration
# python manage.py makemigrations core --name migrate_monthly_status_to_student

"""
Migration 2: Migrate data from StudentMonthlyStatus to Student.monthly_payments
"""

from django.db import migrations, models
from django.db.models import F

def migrate_monthly_status_to_student(apps, schema_editor):
    """
    Migrate all StudentMonthlyStatus records to Student.monthly_payments JSONField
    """
    Student = apps.get_model('core', 'Student')
    StudentMonthlyStatus = apps.get_model('core', 'StudentMonthlyStatus')
    
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
                'last_updated': None,
                'monthly_fee': float(student.monthly_fee)  # Add reference
            }
        
        # Update student with migrated data
        student.monthly_payments = monthly_data
        student.save(update_fields=['monthly_payments'])

def reverse_migrate_monthly_status_to_student(apps, schema_editor):
    """
    Reverse migration: Create StudentMonthlyStatus records from Student.monthly_payments
    """
    Student = apps.get_model('core', 'Student')
    StudentMonthlyStatus = apps.get_model('core', 'StudentMonthlyStatus')
    
    for student in Student.objects.all():
        monthly_payments = student.monthly_payments or {}
        
        for month_key, data in monthly_payments.items():
            year, month = map(int, month_key.split('-'))
            
            # Create or update StudentMonthlyStatus record
            StudentMonthlyStatus.objects.update_or_create(
                student=student,
                year=year,
                month=month,
                defaults={
                    'paid_amount': data.get('amount', 0),
                    'status': data.get('status', 'Unpaid')
                }
            )

class Migration(migrations.Migration):
    dependencies = [
        ('core', 'add_monthly_payments_to_student'),
    ]

    operations = [
        migrations.RunPython(
            migrate_monthly_status_to_student,
            reverse_migrate_monthly_status_to_student
        ),
    ]

# Step 3: Update Views and References (Manual)
# After running migrations, update all code references

# Step 4: Remove StudentMonthlyStatus Model
# python manage.py makemigrations core --name remove_student_monthly_status

"""
Migration 3: Remove StudentMonthlyStatus model and update references
"""

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', 'migrate_monthly_status_to_student'),
    ]

    operations = [
        # Remove any references in other models (if any)
        migrations.RemoveField(
            model_name='draftpayment',
            name='studentmonthlystatus',  # If any foreign keys exist
        ),
        
        # Remove the model
        migrations.DeleteModel(
            'StudentMonthlyStatus',
        ),
    ]
