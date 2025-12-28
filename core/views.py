from django.shortcuts import render, redirect
import json
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import models
from .models import DraftPayment, DraftExpense, Student
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required

def get_next_payment_month_year(student):
    """
    Get the next payment month and year for a student based on their last payment.
    If there's a half-paid month, return that month for completion.
    If no previous payment, return current month and year.
    """
    # Check if student has a payment status
    if student.payment_status in ['Half Paid']:
        # Return the half-paid month for completion
        return student.month, student.year, student.paid_amount
    elif student.payment_status in ['Paid']:
        # Return next month after last payment
        next_month = student.month + 1
        next_year = student.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return next_month, next_year, 0
    else:
        # No payment history - return current month
        today = datetime.now()
        return today.month, today.year, 0

@login_required(login_url='login')
def index(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def add_payment(request):
    error_message = None
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount = request.POST.get('amount')
        monthly_fee = request.POST.get('monthly_fee')
        description = request.POST.get('description')
        month = request.POST.get('month', datetime.now().month)
        year = request.POST.get('year', datetime.now().year)
        
        student = None
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
            except (Student.DoesNotExist, ValueError):
                pass

        # Use provided monthly_fee or fall back to student's monthly fee
        payment_monthly_fee = monthly_fee if monthly_fee else (student.monthly_fee if student else None)

        # Validation: block next-month payment if current month is Half Paid or Unpaid
        if student:
            try:
                target_month = int(month)
                target_year = int(year)
                # Normalize month/year if needed
                if target_month < 1:
                    target_month += 12
                    target_year -= 1
                elif target_month > 12:
                    target_month -= 12
                    target_year += 1

                # Check if there's an existing payment status for the target month
                if student.year == target_year and student.month == target_month and student.payment_status in ['Paid', 'Accepted']:
                    error_message = f"Cannot create new payment for {target_month}/{target_year} - payment is already {student.payment_status}."
                else:
                    # Determine payment status and handle half payments
                    payment_amount = Decimal(amount)
                    monthly_fee_amount = Decimal(payment_monthly_fee) if payment_monthly_fee else Decimal('0')
                    
                    # Calculate total paid after this payment
                    current_paid = student.paid_amount if student.year == target_year and student.month == target_month else Decimal('0')
                    total_paid = current_paid + payment_amount
                    
                    # Determine status based on payment amount
                    if total_paid >= monthly_fee_amount:
                        status = 'Paid'
                        final_amount = monthly_fee_amount  # Don't overpay
                    elif total_paid > 0:
                        status = 'Half Paid'
                        final_amount = total_paid
                    else:
                        status = 'Unpaid'
                        final_amount = Decimal('0')
                    
                    # Update student's monthly status directly
                    student.year = target_year
                    student.month = target_month
                    student.paid_amount = final_amount
                    student.payment_status = status
                    student.save()
                    
                    # Create DraftPayment record
                    DraftPayment.objects.create(
                        user=request.user,
                        student=student,
                        amount=payment_amount,
                        monthly_fee=payment_monthly_fee,
                        description=description,
                        month=month,
                        year=year,
                        status=status  # Set status based on payment logic
                    )

                    if request.headers.get('HX-Request'):
                        response = render(request, 'add_payment.html')
                        response['HX-Trigger'] = 'showDraftToast'
                        return response
                    return redirect('index')
            except (Student.DoesNotExist, ValueError):
                pass
    
    students = Student.objects.all().order_by('name')
    return render(request, 'add_payment.html', {'students': students, 'error_message': error_message})

@login_required(login_url='login')
def get_student_details(request):
    search_type = request.GET.get('search_type', 'student')
    # Support both old and new parameter names for compatibility
    search_query = (
        request.GET.get('search_input', '')
        or request.GET.get('student_name', '')
    ).strip()
    
    if search_type == 'month':
        # Handle month search - return unpaid students for that month
        try:
            # Parse month input like "December 2025"
            month_names = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            parts = search_query.lower().split()
            if len(parts) >= 2:
                month_name = parts[0]
                year = int(parts[1])
                
                if month_name in month_names:
                    month = month_names[month_name]
                    
                    # Get unpaid students for this month
                    unpaid_students = Student.objects.filter(
                        models.Q(year__isnull=True) | models.Q(month__isnull=True) |
                        models.Q(year=year, month=month, payment_status='Unpaid')
                    ).order_by('name')
                    
                    return render(request, 'partials/month_search_results.html', {
                        'unpaid_students': unpaid_students,
                        'month_name': month_name.capitalize(),
                        'year': year,
                        'month': month
                    })
        except (ValueError, IndexError):
            pass
        
        return render(request, 'partials/month_search_results.html', {
            'error': True,
            'search_query': search_query
        })
    
    else:
        # Handle student search (existing functionality)
        try:
            student = Student.objects.get(name__iexact=search_query)
            # Get next payment month and year
            next_month, next_year, remaining_fee = get_next_payment_month_year(student)
            
            context = {
                'student': student,
                'next_month': next_month,
                'next_year': next_year,
                'remaining_fee': remaining_fee
            }
            return render(request, 'partials/student_details.html', context)
        except (Student.DoesNotExist, ValueError):
            return render(request, 'partials/student_details.html', {'student': None})

@login_required(login_url='login')
def get_student_monthly_fee(request):
    student_id = request.GET.get('student_id', '')
    try:
        student = Student.objects.get(pk=student_id)
        if request.headers.get('HX-Request'):
            return HttpResponse(str(student.monthly_fee))
        return HttpResponse(str(student.monthly_fee))
    except (Student.DoesNotExist, ValueError):
        if request.headers.get('HX-Request'):
            return HttpResponse('0')
        return HttpResponse('0')

@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        DraftExpense.objects.create(
            user=request.user,
            name=name,
            amount=amount,
            description=description
        )
        if request.headers.get('HX-Request'):
            response = render(request, 'add_expense.html')
            response['HX-Trigger'] = 'showDraftToast'
            return response
        return redirect('index')
    return render(request, 'add_expense.html')

@login_required(login_url='login')
def view_payments(request):
    # Show only payments that need admin action (Draft, Half Paid, Paid but not yet Accepted)
    payments = DraftPayment.objects.filter(
        status__in=['Draft', 'Half Paid', 'Paid']
    ).exclude(student__isnull=True).order_by('-created_date')
    return render(request, 'view_payments.html', {
        'payments': payments
    })

@login_required(login_url='login')
def view_expenses(request):
    expenses = DraftExpense.objects.filter(status='Draft').order_by('-created_time')
    return render(request, 'view_expenses.html', {
        'expenses': expenses
    })

# Admin Approval Views
@login_required(login_url='login')
def accept_payment(request, pk):
    if request.user.is_staff:
        payment = DraftPayment.objects.get(pk=pk)
        
        # Check if admin adjusted the amount
        if request.method == 'POST':
            adjusted_amount = request.POST.get('adjusted_amount')
            if adjusted_amount:
                payment.amount = adjusted_amount
        
        # Set payment status to Accepted for admin tracking
        payment.status = 'Accepted'
        payment.oath_user = request.user.username
        payment.save()
        
        # Process payment to update StudentMonthlyStatus with correct status
        if payment.student:
            # Temporarily set status to allow process_payment to determine correct status
            original_status = payment.status
            payment.status = 'Draft'  # Reset to draft so process_payment can set correct status
            payment.process_payment()
            # Restore Accepted status for the payment record
            payment.status = original_status
            payment.oath_user = request.user.username
            payment.save()
        
    if request.headers.get('HX-Request'):
        return render(request, 'partials/payment_row.html', {'payment': payment})
    return redirect('view_payments')

@login_required(login_url='login')
def decline_payment(request, pk):
    if request.user.is_staff:
        payment = DraftPayment.objects.get(pk=pk)
        payment.status = 'Declined'
        payment.oath_user = request.user.username
        payment.save()
    if request.headers.get('HX-Request'):
        return render(request, 'partials/payment_row.html', {'payment': payment})
    return redirect('view_payments')

@login_required(login_url='login')
def approve_expense(request, pk):
    if request.user.is_staff:
        expense = DraftExpense.objects.get(pk=pk)
        
        # Check if admin adjusted the amount
        if request.method == 'POST':
            adjusted_amount = request.POST.get('adjusted_amount')
            if adjusted_amount:
                expense.amount = adjusted_amount
        
        expense.status = 'Accepted'
        expense.oath_user = request.user.username
        expense.save()
    if request.headers.get('HX-Request'):
        return render(request, 'partials/expense_row.html', {'expense': expense})
    return redirect('view_expenses')

@login_required(login_url='login')
def decline_expense(request, pk):
    if request.user.is_staff:
        expense = DraftExpense.objects.get(pk=pk)
        expense.status = 'Declined'
        expense.oath_user = request.user.username
        expense.save()
    if request.headers.get('HX-Request'):
        return render(request, 'partials/expense_row.html', {'expense': expense})
    return redirect('view_expenses')

@login_required(login_url='login')
def view_confirmed(request):
    payments = DraftPayment.objects.filter(status__in=['Paid', 'Half Paid', 'Accepted']).exclude(student__isnull=True).order_by('-created_date')
    expenses = DraftExpense.objects.filter(status='Accepted').order_by('-created_time')
    return render(request, 'confirmed_transactions.html', {
        'payments': payments,
        'expenses': expenses
    })

@login_required(login_url='login')
def view_confirmed_payments(request):
    payments = DraftPayment.objects.filter(status__in=['Paid', 'Half Paid', 'Accepted']).exclude(student__isnull=True).order_by('-created_date')
    return render(request, 'confirmed_payments.html', {
        'payments': payments
    })

@login_required(login_url='login')
def view_confirmed_expenses(request):
    expenses = DraftExpense.objects.filter(status='Accepted').order_by('-created_time')
    return render(request, 'confirmed_expenses.html', {
        'expenses': expenses
    })

from django.db.models import Sum, functions
from datetime import datetime

@login_required(login_url='login')
def analyze_view(request):
    # Get selected year from query parameter or default to current year
    selected_year = request.GET.get('year', datetime.now().year)
    try:
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
    
    # Get all available years with data
    available_years = set()
    payment_years = DraftPayment.objects.filter(status__in=['Paid', 'Half Paid']).values_list('year', flat=True).distinct()
    expense_years = DraftExpense.objects.filter(status='Accepted').dates('created_time', 'year')
    available_years.update(payment_years)
    available_years.update(expense_years.year for expense_years in expense_years)
    
    # Add current year if not present
    available_years.add(datetime.now().year)
    
    available_years = sorted(available_years, reverse=True)
    
    # Prepare data for selected year
    # Get confirmed payments for this year
    confirmed_payments = DraftPayment.objects.filter(
        status__in=['Paid', 'Half Paid', 'Accepted'],
        year=selected_year
    ).exclude(student__isnull=True).order_by('month', 'created_date')
    
    # Get confirmed expenses for this year
    confirmed_expenses = DraftExpense.objects.filter(
        status='Accepted',
        created_time__year=selected_year
    ).order_by('created_time')
    
    # Calculate monthly totals
    monthly_totals = {}
    for month in range(1, 13):
        monthly_totals[month] = {
            'month_name': datetime(selected_year, month, 1).strftime('%B'),
            'total_payments': 0,
            'total_expenses': 0,
            'net': 0
        }
    
    # Sum payments by month
    for payment in confirmed_payments:
        monthly_totals[payment.month]['total_payments'] += float(payment.amount)
    
    # Sum expenses by month
    for expense in confirmed_expenses:
        month = expense.created_time.month
        monthly_totals[month]['total_expenses'] += float(expense.amount)
    
    # Calculate net for each month
    for month_data in monthly_totals.values():
        month_data['net'] = month_data['total_payments'] - month_data['total_expenses']
    
    # Calculate yearly totals
    yearly_total_payments = sum(data['total_payments'] for data in monthly_totals.values())
    yearly_total_expenses = sum(data['total_expenses'] for data in monthly_totals.values())
    yearly_net = yearly_total_payments - yearly_total_expenses
    
    # Get annual report using simple queries
    annual_report_data = []
    for month in range(1, 13):
        total_students = Student.objects.count()
        paid_students = Student.objects.filter(year=selected_year, month=month, payment_status='Paid').count()
        half_paid_students = Student.objects.filter(year=selected_year, month=month, payment_status='Half Paid').count()
        unpaid_students = Student.objects.filter(
            models.Q(year__isnull=True) | models.Q(month__isnull=True) | 
            models.Q(year=selected_year, month=month, payment_status='Unpaid')
        ).count()
        
        total_collected = Student.objects.filter(
            year=selected_year, month=month, payment_status__in=['Paid', 'Half Paid']
        ).aggregate(total=models.Sum('paid_amount'))['total'] or 0
        
        annual_report_data.append({
            'month': month,
            'total_students': total_students,
            'paid_students': paid_students,
            'half_paid_students': half_paid_students,
            'unpaid_students': unpaid_students,
            'total_collected': total_collected
        })
    
    return render(request, 'analyze.html', {
        'monthly_totals': monthly_totals,
        'yearly_total_payments': yearly_total_payments,
        'yearly_total_expenses': yearly_total_expenses,
        'yearly_net': yearly_net,
        'confirmed_payments': confirmed_payments,
        'confirmed_expenses': confirmed_expenses,
        'annual_report': annual_report_data,
        'selected_year': selected_year,
        'available_years': available_years
    })

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if len(password) < 4:
            return render(request, 'signup.html', {'error': 'Password must be at least 4 characters.'})
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists.'})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('index')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')

@login_required(login_url='login')
def view_students(request):
    students = Student.objects.all().order_by('name')
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    for s in students:
        s.last_paid_month = DraftPayment.get_last_paid_month(s)
    return render(request, 'students.html', {'students': students, 'month_names': month_names})

@login_required(login_url='login')
def add_student(request):
    if not request.user.is_staff:
        return redirect('view_students')
    
    if request.method == 'POST':
        name = request.POST.get('name', '')
        fixed_fee = request.POST.get('monthly_fee')
        Student.objects.create(
            name=name,
            monthly_fee=fixed_fee
        )
        if request.headers.get('HX-Request'):
            response = render(request, 'students.html', {'students': Student.objects.all().order_by('name')})
            response['HX-Trigger'] = json.dumps({
                "showToast": {
                    "message": "Student added",
                    "type": "success"
                }
            })
            return response
        return redirect('view_students')
    
    return render(request, 'student_form.html', {'title': 'Add Student', 'is_update': False})

@login_required(login_url='login')
def update_student(request, pk):
    if not request.user.is_staff:
        return redirect('view_students')
    
    student = Student.objects.get(pk=pk)
    if request.method == 'POST':
        student.name = request.POST.get('name', '')
        student.monthly_fee = request.POST.get('monthly_fee')
        student.save()
        if request.headers.get('HX-Request'):
            response = render(request, 'students.html', {'students': Student.objects.all().order_by('name')})
            response['HX-Trigger'] = json.dumps({
                "showToast": {
                    "message": "Student updated",
                    "type": "success"
                }
            })
            return response
        return redirect('view_students')
    
    return render(request, 'student_form.html', {'title': 'Update Student', 'student': student, 'is_update': True})

@login_required(login_url='login')
def delete_student(request, pk):
    if request.user.is_staff:
        Student.objects.get(pk=pk).delete()
    
    if request.headers.get('HX-Request'):
        response = HttpResponse("")
        response['HX-Trigger'] = json.dumps({
            "showToast": {
                "message": "Student deleted",
                "type": "error"
            }
        })
        return response
        
    return redirect('view_students')

@login_required(login_url='login')
def search_students(request):
    return render(request, 'search_students.html')

@login_required(login_url='login')
def search_student_details(request):
    search_type = request.GET.get('search_type', 'student').strip() or 'student'
    search_query = (
        request.GET.get('search_input', '')
        or request.GET.get('search_name', '')
    ).strip()

    if search_type == 'month':
        try:
            month_names = {
                'january': 1,
                'february': 2,
                'march': 3,
                'april': 4,
                'may': 5,
                'june': 6,
                'july': 7,
                'august': 8,
                'september': 9,
                'october': 10,
                'november': 11,
                'december': 12,
            }

            parts = search_query.lower().split()
            if len(parts) >= 2:
                month_name = parts[0]
                year = int(parts[1])

                if month_name in month_names:
                    month = month_names[month_name]
                    paid_statuses = ['Paid', 'Half Paid', 'Accepted']

                    unpaid_students = Student.objects.exclude(
                        year=year,
                        month=month,
                        payment_status__in=paid_statuses,
                    ).order_by('name')

                    return render(request, 'partials/month_search_results.html', {
                        'unpaid_students': unpaid_students,
                        'month_name': month_name.capitalize(),
                        'year': year,
                        'month': month,
                    })
        except Exception:
            pass

        return render(request, 'partials/month_search_results.html', {
            'error': True,
            'search_query': search_query,
        })

    student = None
    last_paid_month = None
    current_month_status = None
    selected_year = datetime.now().year

    if search_query:
        try:
            student = Student.objects.get(name__iexact=search_query)
            last_paid_data = DraftPayment.get_last_paid_month(student)
            if last_paid_data:
                last_paid_month = {
                    'year': last_paid_data['year'],
                    'month': last_paid_data['month'],
                    'status': last_paid_data['status'],
                    'amount': last_paid_data['amount'],
                }

            current_month = datetime.now().month
            current_year = datetime.now().year
            if student.year == current_year and student.month == current_month:
                current_month_status = {
                    'status': student.payment_status,
                    'amount': student.paid_amount,
                }
        except Student.DoesNotExist:
            pass

    return render(request, 'partials/search_student_results.html', {
        'student': student,
        'search_query': search_query,
        'last_paid_month': last_paid_month,
        'current_month_status': current_month_status,
        'selected_year': selected_year,
    })

@login_required(login_url='login')
def student_annual_report(request):
    student_id = request.GET.get('student_id')
    year = request.GET.get('year', datetime.now().year)

    try:
        year = int(year)
    except (TypeError, ValueError):
        year = datetime.now().year

    student = None
    if student_id:
        try:
            student = Student.objects.get(pk=student_id)
        except (Student.DoesNotExist, ValueError):
            student = None

    months = []
    if student:
        for month in range(1, 13):
            # Check if this month/year matches the student's payment data
            if student.year == year and student.month == month:
                months.append({
                    'month': month,
                    'month_name': datetime(year, month, 1).strftime('%B'),
                    'status': student.payment_status,
                    'paid_amount': student.paid_amount,
                })
            else:
                months.append({
                    'month': month,
                    'month_name': datetime(year, month, 1).strftime('%B'),
                    'status': 'Unpaid',
                    'paid_amount': 0,
                })

    return render(request, 'partials/student_annual_report.html', {
        'student': student,
        'year': year,
        'months': months,
    })

def logout_view(request):
    logout(request)
    return redirect('index')
