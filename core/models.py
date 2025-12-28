from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

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

        # Update student's monthly payment status directly
        self.student.year = self.year
        self.student.month = self.month
        self.student.paid_amount = amount_paid
        self.student.payment_status = self.status
        self.student.save()

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

    @staticmethod
    def get_last_paid_month(student):
        """Get the last paid month for a student"""
        if student.payment_status in ['Paid', 'Half Paid', 'Accepted'] and student.year and student.month:
            return {
                'year': student.year,
                'month': student.month,
                'status': student.payment_status,
                'amount': student.paid_amount
            }
        return None

    @staticmethod
    def get_annual_report(year):
        """Get annual report grouped by month"""
        # This will be implemented in views using Student methods
        return []

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
    Student model with integrated monthly payment tracking.
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
    
    # Monthly payment tracking columns (from old StudentMonthlyStatus)
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')

    class Meta:
        db_table = 'core_student'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class HolidayMonth(models.Model):
    """
    Holiday months where students don't need to pay fees.
    """
    MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]

    year = models.IntegerField()
    month = models.IntegerField(choices=MONTH_CHOICES)
    reason = models.TextField(blank=True, help_text="Optional reason for the holiday")
    
    DISCOUNT_TYPE_CHOICES = [
        ('Full', 'Full Holiday (100% Off)'),
        ('Percentage', 'Percentage Discount (%)'),
        ('Amount', 'Fixed Amount Discount (Rs)'),
    ]
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='Full')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Value for percentage or amount discount")
    
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_holidaymonth'
        unique_together = ['year', 'month']
        ordering = ['-year', 'month']
        indexes = [
            models.Index(fields=['year', 'month']),
        ]

    def __str__(self):
        return f"{self.get_month_display()} {self.year}"

    @property
    def month_name(self):
        return self.get_month_display()


class StudentDiscount(models.Model):
    """
    Student-specific discounts for specific months.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='discounts')
    year = models.IntegerField()
    month = models.IntegerField(choices=HolidayMonth.MONTH_CHOICES)
    reason = models.TextField(blank=True, help_text="Optional reason for the discount")
    
    DISCOUNT_TYPE_CHOICES = HolidayMonth.DISCOUNT_TYPE_CHOICES
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='Full')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Value for percentage or amount discount")
    
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_studentdiscount'
        unique_together = ['student', 'year', 'month']
        ordering = ['-year', 'month', 'student__name']
        indexes = [
            models.Index(fields=['student', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.get_month_display()} {self.year}"

    @property
    def month_name(self):
        return self.get_month_display()

