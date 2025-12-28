import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

# Add monthly_payments column to core_student table manually
def add_monthly_payments_column():
    with connection.cursor() as cursor:
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'core_student' AND column_name = 'monthly_payments'
        """)
        
        if cursor.fetchone():
            print("Column monthly_payments already exists")
            return
        
        # Add the column
        cursor.execute("""
            ALTER TABLE core_student 
            ADD COLUMN monthly_payments JSONB DEFAULT '{}'
        """)
        
        print("Added monthly_payments column to core_student table")

if __name__ == "__main__":
    add_monthly_payments_column()
