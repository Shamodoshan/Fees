from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

def get_first_of_month():
    return date.today().replace(day=1)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Partial', 'Partial'),
        ('Declined', 'Declined'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True)
    student_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Payment: {self.student_name} - {self.amount} ({self.status})"

class Expense(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    expense_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Expense: {self.expense_name} - {self.amount} ({self.status})"

class Student(models.Model):
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
