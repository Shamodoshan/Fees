from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

def get_first_of_month():
    return date.today().replace(day=1)

class Payment(models.Model):
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
<<<<<<< Updated upstream
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
=======
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    month = models.IntegerField()
    year = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='user_id')
    oath_user = models.CharField(max_length=255, blank=True, null=True)
>>>>>>> Stashed changes

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
        """Process payment acceptance and update monthly status"""
        if not self.student:
            return

        # Ensure valid month/year before writing StudentMonthlyStatus
        self.year, self.month = DraftPayment.normalize_month_year(self.year, self.month)

        # Use payment's monthly_fee if set, otherwise fall back to student's monthly_fee
        monthly_fee = self.monthly_fee if self.monthly_fee else self.student.monthly_fee
        amount_paid = self.amount

        # Get or create monthly status record
        monthly_status, created = StudentMonthlyStatus.objects.get_or_create(
            student=self.student,
            year=self.year,
            month=self.month,
            defaults={'paid_amount': 0, 'status': 'Unpaid'}
        )

        if amount_paid >= monthly_fee:
            # Full payment
            monthly_status.paid_amount = monthly_fee
            monthly_status.status = 'Paid'
            # Only update payment status if not already accepted by admin
            if self.status != 'Accepted':
                self.status = 'Paid'
        else:
            # Partial payment
            monthly_status.paid_amount += amount_paid
            if monthly_status.paid_amount >= monthly_fee:
                monthly_status.paid_amount = monthly_fee
                monthly_status.status = 'Paid'
                # Only update payment status if not already accepted by admin
                if self.status != 'Accepted':
                    self.status = 'Paid'
            else:
                monthly_status.status = 'Half Paid'
                # Only update payment status if not already accepted by admin
                if self.status != 'Accepted':
                    self.status = 'Half Paid'

        monthly_status.save()

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
        return StudentMonthlyStatus.objects.filter(
            student=student, 
            status__in=['Paid', 'Half Paid', 'Accepted']
        ).order_by('-year', '-month').first()

    @staticmethod
    def get_annual_report(year):
        """Get annual report grouped by month"""
        return StudentMonthlyStatus.objects.filter(
            year=year
        ).values('month').annotate(
            total_students=models.Count('student'),
            paid_students=models.Count('student', filter=models.Q(status='Paid')),
            half_paid_students=models.Count('student', filter=models.Q(status='Half Paid')),
            unpaid_students=models.Count('student', filter=models.Q(status='Unpaid')),
            total_collected=models.Sum('paid_amount')
        ).order_by('month')

class Expense(models.Model):
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
<<<<<<< Updated upstream
    name = models.CharField(max_length=200)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2)
    temporary_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_paid_date = models.DateField(default=get_first_of_month)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property
    def full_name(self):
        return self.name
=======
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class StudentMonthlyStatus(models.Model):
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Half Paid', 'Half Paid'),
        ('Paid', 'Paid'),
    ]
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, db_column='student_id')
    year = models.IntegerField()
    month = models.IntegerField()
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unpaid')

    class Meta:
        unique_together = ['student', 'year', 'month']

    def __str__(self):
        return f"{self.student.name} - {self.year}/{self.month}: {self.status}"
>>>>>>> Stashed changes
