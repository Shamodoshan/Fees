# NEW MODELS.PY - Optimized Student Model with Monthly Tracking

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from django.core.serializers.json import DjangoJSONEncoder
import json

def get_first_of_month():
    return date.today().replace(day=1)

class DraftPayment(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Accepted', 'Accepted'),
        ('Partial', 'Partial'),
        ('Declined', 'Declined'),
        ('Half Paid', 'Half Paid'),
    ]
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, db_column='student_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Monthly fee for this payment period")
    created_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    month = models.IntegerField()
    year = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='user_id')
    oath_user = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Payment: {self.student.name if self.student else 'Unknown'} - {self.amount} ({self.status})"

    def get_suggested_amount(self):
        """Suggest monthly fee amount for this student"""
        if self.student:
            return self.student.monthly_fee
        return 0

    def save(self, *args, **kwargs):
        # Normalize month/year in case month goes beyond 12 (e.g., 13 => Jan next year)
        self.year, self.month = DraftPayment.normalize_month_year(self.year, self.month)

        # When payment is accepted, process the payment logic
        if self.status == 'Accepted' and self.student:
            self.process_payment()
        super().save(*args, **kwargs)

    def process_payment(self):
        """Process payment acceptance and update student's monthly status"""
        if not self.student:
            return

        # Ensure valid month/year before updating student status
        self.year, self.month = DraftPayment.normalize_month_year(self.year, self.month)

        # Use payment's monthly_fee if set, otherwise fall back to student's monthly_fee
        monthly_fee = self.monthly_fee if self.monthly_fee else self.student.monthly_fee
        amount_paid = self.amount

        # Update student's monthly payment status
        self.student.update_monthly_status(
            year=self.year,
            month=self.month,
            amount_paid=amount_paid,
            monthly_fee=monthly_fee,
            payment_status=self.status
        )

    @staticmethod
    def normalize_month_year(year, month):
        """Normalize month/year so month is always 1..12.

        Examples:
        - (2025, 13) => (2026, 1)
        - (2025, 0)  => (2024, 12)
        """
        try:
            year = int(year)
            month = int(month)
        except (TypeError, ValueError):
            return year, month

        total = (year * 12) + (month - 1)
        new_year = total // 12
        new_month = (total % 12) + 1
        return new_year, new_month

class DraftExpense(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    ]
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_time = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='user_id')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    oath_user = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Expense: {self.name} - {self.amount} ({self.status})"

class Student(models.Model):
    """
    Optimized Student model with integrated monthly payment tracking using JSONField.
    """
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Half Paid', 'Half Paid'),
        ('Paid', 'Paid'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    created_date = models.DateTimeField(default=timezone.now)
    
    # Monthly payment tracking stored as JSON
    # Structure: {"YYYY-MM": {"status": "Paid", "amount": 5000, "paid_date": "2025-12-28"}}
    monthly_payments = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Monthly payment status and amounts in JSON format"
    )
    
    # Cache for frequently accessed data
    _last_paid_month = None
    _monthly_cache = {}

    class Meta:
        db_table = 'core_student'
        indexes = [
            models.Index(fields=['name']),
            # PostgreSQL GIN index for efficient JSON queries
            models.Index(fields=['monthly_payments'], name='idx_student_monthly_payments', 
                         opclasses=['jsonb_path_ops']) if hasattr(models.Index, 'opclasses') else models.Index(fields=['monthly_payments'])
        ]

    def __str__(self):
        return self.name

    def get_month_key(self, year, month):
        """Generate standardized month key for JSON storage"""
        return f"{year:04d}-{month:02d}"

    def update_monthly_status(self, year, month, amount_paid, monthly_fee, payment_status='Draft'):
        """
        Update or create monthly payment status for this student.
        
        Args:
            year: Year (int)
            month: Month (int)
            amount_paid: Amount paid in this transaction (Decimal)
            monthly_fee: Monthly fee amount (Decimal)
            payment_status: Current payment status (str)
        """
        month_key = self.get_month_key(year, month)
        
        # Get current monthly data or create new
        monthly_data = self.monthly_payments.get(month_key, {
            'status': 'Unpaid',
            'amount': 0,
            'paid_date': None,
            'last_updated': None
        })
        
        # Calculate total paid amount
        current_paid = monthly_data.get('amount', 0)
        total_paid = current_paid + amount_paid
        
        # Determine new status
        if payment_status == 'Accepted':
            # Admin accepted payment - use total logic
            if total_paid >= monthly_fee:
                new_status = 'Paid'
                final_amount = monthly_fee
            elif total_paid > 0:
                new_status = 'Half Paid'
                final_amount = total_paid
            else:
                new_status = 'Unpaid'
                final_amount = 0
        else:
            # For other statuses, preserve existing logic
            if payment_status in ['Paid', 'Half Paid']:
                new_status = payment_status
                final_amount = total_paid if total_paid <= monthly_fee else monthly_fee
            else:
                new_status = 'Unpaid'
                final_amount = total_paid

        # Update monthly data
        monthly_data.update({
            'status': new_status,
            'amount': final_amount,
            'paid_date': timezone.now().isoformat(),
            'last_updated': timezone.now().isoformat(),
            'monthly_fee': float(monthly_fee)  # Store monthly fee for reference
        })
        
        # Update the JSON field
        self.monthly_payments[month_key] = monthly_data
        self.save(update_fields=['monthly_payments'])
        
        # Clear cache
        self._last_paid_month = None
        if month_key in self._monthly_cache:
            del self._monthly_cache[month_key]

    def get_monthly_status(self, year, month):
        """Get payment status for a specific month"""
        month_key = self.get_month_key(year, month)
        
        # Check cache first
        if month_key in self._monthly_cache:
            return self._monthly_cache[month_key]
        
        # Get from JSON field
        monthly_data = self.monthly_payments.get(month_key, {
            'status': 'Unpaid',
            'amount': 0,
            'paid_date': None
        })
        
        # Cache the result
        self._monthly_cache[month_key] = monthly_data
        return monthly_data

    def get_last_paid_month(self):
        """Get the last month with any payment activity"""
        if self._last_paid_month:
            return self._last_paid_month
        
        # Find all months with payments
        paid_months = []
        for month_key, data in self.monthly_payments.items():
            if data.get('status') in ['Paid', 'Half Paid']:
                year, month = map(int, month_key.split('-'))
                paid_months.append((year, month, data))
        
        # Sort by year, month descending and get first
        if paid_months:
            paid_months.sort(key=lambda x: (x[0], x[1]), reverse=True)
            self._last_paid_month = paid_months[0]  # (year, month, data)
        else:
            self._last_paid_month = None
            
        return self._last_paid_month

    def get_payment_history(self, limit_months=12):
        """Get payment history for the last N months"""
        history = []
        current_date = date.today()
        
        for i in range(limit_months):
            # Calculate month/year going backwards
            total_months = (current_date.year * 12) + (current_date.month - 1) - i
            year = total_months // 12
            month = (total_months % 12) + 1
            
            status_data = self.get_monthly_status(year, month)
            history.append({
                'year': year,
                'month': month,
                'status': status_data.get('status', 'Unpaid'),
                'amount': status_data.get('amount', 0),
                'paid_date': status_data.get('paid_date')
            })
        
        return history

    @classmethod
    def get_unpaid_students_for_month(cls, year, month):
        """
        Get all students who haven't paid for a specific month.
        Optimized query using JSON field operations.
        """
        month_key = f"{year:04d}-{month:02d}"
        
        # PostgreSQL-specific JSON query for unpaid students
        from django.db.models import Q
        
        # Students without the month key OR with unpaid status
        unpaid_students = cls.objects.filter(
            Q(monthly_payments__isnull=True) |
            ~Q(monthly_payments__has_key=month_key) |
            Q(**{f"monthly_payments__{month_key}__status": "Unpaid"})
        )
        
        return unpaid_students

    @classmethod
    def get_paid_students_for_month(cls, year, month):
        """Get all students who have paid (fully or partially) for a specific month"""
        month_key = f"{year:04d}-{month:02d}"
        
        from django.db.models import Q
        
        paid_students = cls.objects.filter(
            Q(**{f"monthly_payments__{month_key}__status": "Paid"}) |
            Q(**{f"monthly_payments__{month_key}__status": "Half Paid"})
        )
        
        return paid_students

    @classmethod
    def get_monthly_report(cls, year, month):
        """Get comprehensive monthly report"""
        month_key = f"{year:04d}-{month:02d}"
        
        from django.db.models import Q, Count, Sum, Case, When, Value, IntegerField
        
        # Use PostgreSQL JSON aggregation functions
        report = cls.objects.aggregate(
            total_students=Count('id'),
            paid_students=Count(
                Case(
                    When(Q(**{f"monthly_payments__{month_key}__status": "Paid"}), then=Value(1)),
                    output_field=IntegerField()
                )
            ),
            half_paid_students=Count(
                Case(
                    When(Q(**{f"monthly_payments__{month_key}__status": "Half Paid"}), then=Value(1)),
                    output_field=IntegerField()
                )
            ),
            unpaid_students=Count(
                Case(
                    When(
                        Q(~Q(monthly_payments__has_key=month_key) | Q(**{f"monthly_payments__{month_key}__status": "Unpaid"}))
                    , then=Value(1)
                ),
                output_field=IntegerField()
            ),
            total_collected=Sum(
                Case(
                    When(
                        Q(**{f"monthly_payments__{month_key}__status__in": ["Paid", "Half Paid"]}),
                        then=f"monthly_payments__{month_key}__amount"
                    ),
                    output_field=models.DecimalField()
                )
            )
        )
        
        return report

    @classmethod
    def get_annual_report(cls, year):
        """Get annual report with monthly breakdown"""
        # This would be more complex with JSON, but here's the approach:
        # We'd need to extract all month keys for the year and aggregate
        
        # Alternative: Use Raw SQL with PostgreSQL JSON functions
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    EXTRACT(MONTH FROM key::date) as month,
                    COUNT(*) as total_students,
                    COUNT(CASE WHEN value->>'status' = 'Paid' THEN 1 END) as paid_students,
                    COUNT(CASE WHEN value->>'status' = 'Half Paid' THEN 1 END) as half_paid_students,
                    COUNT(CASE WHEN value->>'status' = 'Unpaid' OR value IS NULL THEN 1 END) as unpaid_students,
                    COALESCE(SUM(CASE WHEN value->>'status' IN ('Paid', 'Half Paid') 
                        THEN (value->>'amount')::decimal ELSE 0 END), 0) as total_collected
                FROM core_student, jsonb_each_text(monthly_payments)
                WHERE key LIKE %s
                GROUP BY EXTRACT(MONTH FROM key::date)
                ORDER BY month
            """, [f"{year}-%"])
            
            results = cursor.fetchall()
        
        # Convert to list of dicts
        report = []
        for row in results:
            report.append({
                'month': int(row[0]),
                'total_students': row[1],
                'paid_students': row[2],
                'half_paid_students': row[3],
                'unpaid_students': row[4],
                'total_collected': row[5]
            })
        
        return report
