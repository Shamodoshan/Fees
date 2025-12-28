from django.shortcuts import render, redirect
import json
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
<<<<<<< Updated upstream
from .models import Payment, Expense, Student
=======
from .models import DraftPayment, DraftExpense, Student, StudentMonthlyStatus
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
>>>>>>> Stashed changes

from django.contrib.auth.decorators import login_required

def get_next_payment_month_year(student):
    """
    Get the next payment month and year for a student based on their last payment.
    If there's a half-paid month, return that month for completion.
    If no previous payment, return current month and year.
    """
    # First check if there's any half-paid month that needs completion
    half_paid_status = StudentMonthlyStatus.objects.filter(
        student=student, 
        status='Half Paid'
    ).order_by('year', 'month').first()
    
    if half_paid_status:
        # Return the half-paid month for completion
        return half_paid_status.month, half_paid_status.year
    
    # If no half-paid months, find the last confirmed payment from StudentMonthlyStatus
    last_status = StudentMonthlyStatus.objects.filter(
        student=student, 
        status__in=['Paid', 'Half Paid', 'Accepted']
    ).order_by('-year', '-month').first()
    
    if last_status:
        # Get next month after last payment
        next_month = last_status.month + 1
        next_year = last_status.year
        
        # Handle year transition
        if next_month > 12:
            next_month = 1
            next_year += 1
            
        return next_month, next_year
    else:
        # No previous payment, use current month/year
        return datetime.now().month, datetime.now().year

@login_required(login_url='login')
def index(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def add_payment(request):
    error_message = None
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount = request.POST.get('amount')
<<<<<<< Updated upstream
        year = request.POST.get('year')
        month = request.POST.get('month')
=======
        monthly_fee = request.POST.get('monthly_fee')
>>>>>>> Stashed changes
        description = request.POST.get('description')
        month = request.POST.get('month', datetime.now().month)
        year = request.POST.get('year', datetime.now().year)
        
        student = None
        if student_id:
            try:
                student = Student.objects.get(pk=student_id)
            except (Student.DoesNotExist, ValueError):
                pass

<<<<<<< Updated upstream
        Payment.objects.create(
            user=request.user,
            student=student,
            student_name=student_name,
            amount=amount,
            year=year,
            month=month,
            description=description
        )
        if request.headers.get('HX-Request'):
            response = render(request, 'add_payment.html')
            response['HX-Trigger'] = 'showDraftToast'
            return response
        return redirect('index')
    return render(request, 'add_payment.html')
=======
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

                # Find previous month
                prev_month = target_month - 1
                prev_year = target_year
                if prev_month < 1:
                    prev_month += 12
                    prev_year -= 1

                prev_status = StudentMonthlyStatus.objects.filter(
                    student=student,
                    month=prev_month,
                    year=prev_year
                ).first()

                if prev_status and prev_status.status in ('Half Paid', 'Unpaid'):
                    error_message = f"Cannot pay for {target_month}/{target_year} because previous month ({prev_month}/{prev_year}) is {prev_status.status}. Please complete the previous payment first."
            except (TypeError, ValueError):
                pass

        if not error_message:
            # Determine payment status and handle half payments
            payment_amount = Decimal(amount)
            monthly_fee_amount = Decimal(payment_monthly_fee) if payment_monthly_fee else Decimal('0')
            
            # Get or create StudentMonthlyStatus for this month
            monthly_status, created = StudentMonthlyStatus.objects.get_or_create(
                student=student,
                month=target_month,
                year=target_year,
                defaults={'paid_amount': Decimal('0'), 'status': 'Unpaid'}
            )
            
            # Calculate total paid after this payment
            total_paid = monthly_status.paid_amount + payment_amount
            
            # Determine status based on payment amount
            if total_paid >= monthly_fee_amount:
                status = 'Paid'
                paid_amount = monthly_fee_amount  # Don't overpay
            elif total_paid > 0:
                status = 'Half Paid'
                paid_amount = total_paid
            else:
                status = 'Unpaid'
                paid_amount = Decimal('0')
            
            # Update StudentMonthlyStatus
            monthly_status.paid_amount = paid_amount
            monthly_status.status = status
            monthly_status.save()
            
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
    
    students = Student.objects.all().order_by('name')
    return render(request, 'add_payment.html', {'students': students, 'error_message': error_message})
>>>>>>> Stashed changes

@login_required(login_url='login')
def get_student_details(request):
    student_name = request.GET.get('student_name', '').strip()
    try:
<<<<<<< Updated upstream
        # Search by name
        student = Student.objects.filter(name__icontains=student_name).first()
        return render(request, 'partials/student_details.html', {'student': student})
    except (ValueError):
=======
        student = Student.objects.get(name=student_name)
        # Get next payment month and year
        next_month, next_year = get_next_payment_month_year(student)
        
        # Check if there's a half-paid status for the next month
        monthly_status = StudentMonthlyStatus.objects.filter(
            student=student,
            month=next_month,
            year=next_year
        ).first()
        
        remaining_fee = 0
        if monthly_status and monthly_status.status == 'Half Paid':
            remaining_fee = student.monthly_fee - monthly_status.paid_amount
        
        context = {
            'student': student,
            'next_month': next_month,
            'next_year': next_year,
            'remaining_fee': remaining_fee
        }
        return render(request, 'partials/student_details.html', context)
    except (Student.DoesNotExist, ValueError):
>>>>>>> Stashed changes
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
        Expense.objects.create(
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
<<<<<<< Updated upstream
    payments = Payment.objects.filter(status='Pending').order_by('-created_at')
=======
    # Show only payments that need admin action (Draft, Half Paid, Paid but not yet Accepted)
    payments = DraftPayment.objects.filter(
        status__in=['Draft', 'Half Paid', 'Paid']
    ).exclude(student__isnull=True).order_by('-created_date')
    
>>>>>>> Stashed changes
    return render(request, 'view_payments.html', {
        'payments': payments
    })

@login_required(login_url='login')
def view_expenses(request):
<<<<<<< Updated upstream
    expenses = Expense.objects.filter(status='Pending').order_by('-created_at')
=======
    expenses = DraftExpense.objects.filter(status='Draft').order_by('-created_time')
>>>>>>> Stashed changes
    return render(request, 'view_expenses.html', {
        'expenses': expenses
    })

# Admin Approval Views
@login_required(login_url='login')
def accept_payment(request, pk):
    if request.user.is_staff:
        payment = Payment.objects.get(pk=pk)
        
        # Check if admin adjusted the amount
        if request.method == 'POST':
            adjusted_amount = request.POST.get('adjusted_amount')
            if adjusted_amount:
                payment.amount = adjusted_amount
        
        payment.status = 'Accepted'
        payment.oath_user = request.user.username
        payment.save()  # This will trigger the process_payment method
        
        # Ensure the payment is processed
        if payment.student:
            payment.process_payment()
            payment.save()
        
    if request.headers.get('HX-Request'):
        return render(request, 'partials/payment_row.html', {'payment': payment})
    return redirect('view_payments')

@login_required(login_url='login')
def decline_payment(request, pk):
    if request.user.is_staff:
        payment = Payment.objects.get(pk=pk)
        payment.status = 'Declined'
        payment.oath_user = request.user.username
        payment.save()
    if request.headers.get('HX-Request'):
        return render(request, 'partials/payment_row.html', {'payment': payment})
    return redirect('view_payments')

@login_required(login_url='login')
def approve_expense(request, pk):
    if request.user.is_staff:
        expense = Expense.objects.get(pk=pk)
        
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
        expense = Expense.objects.get(pk=pk)
        expense.status = 'Declined'
        expense.oath_user = request.user.username
        expense.save()
    if request.headers.get('HX-Request'):
        return render(request, 'partials/expense_row.html', {'expense': expense})
    return redirect('view_expenses')

@login_required(login_url='login')
def view_confirmed(request):
<<<<<<< Updated upstream
    payments = Payment.objects.filter(status='Accepted').order_by('-created_at')
    expenses = Expense.objects.filter(status='Accepted').order_by('-created_at')
=======
    payments = DraftPayment.objects.filter(status__in=['Paid', 'Half Paid', 'Accepted']).exclude(student__isnull=True).order_by('-created_date')
    expenses = DraftExpense.objects.filter(status='Accepted').order_by('-created_time')
>>>>>>> Stashed changes
    return render(request, 'confirmed_transactions.html', {
        'payments': payments,
        'expenses': expenses
    })

@login_required(login_url='login')
def view_confirmed_payments(request):
<<<<<<< Updated upstream
    payments = Payment.objects.filter(status='Accepted').order_by('-created_at')
=======
    payments = DraftPayment.objects.filter(status__in=['Paid', 'Half Paid', 'Accepted']).exclude(student__isnull=True).order_by('-created_date')
>>>>>>> Stashed changes
    return render(request, 'confirmed_payments.html', {
        'payments': payments
    })

@login_required(login_url='login')
def view_confirmed_expenses(request):
<<<<<<< Updated upstream
    expenses = Expense.objects.filter(status='Accepted').order_by('-created_at')
=======
    expenses = DraftExpense.objects.filter(status='Accepted').order_by('-created_time')
>>>>>>> Stashed changes
    return render(request, 'confirmed_expenses.html', {
        'expenses': expenses
    })

from django.db.models import Sum, functions
from datetime import datetime

@login_required(login_url='login')
def analyze_view(request):
<<<<<<< Updated upstream
    # Aggregate payments by month and year
    payment_stats = Payment.objects.filter(status='Accepted').annotate(
        month=functions.TruncMonth('created_at')
    ).values('month').annotate(total=Sum('amount')).order_by('-month')

    # Aggregate expenses by month and year
    expense_stats = Expense.objects.filter(status='Accepted').annotate(
        month=functions.TruncMonth('created_at')
    ).values('month').annotate(total=Sum('amount')).order_by('-month')

    # Combine data by month
    monthly_data = {}
    for p in payment_stats:
        m_str = p['month'].strftime('%B %Y')
        monthly_data[m_str] = {'month_obj': p['month'], 'payments': p['total'], 'expenses': 0}
=======
    # Get selected year from query parameter or default to current year
    selected_year = request.GET.get('year', datetime.now().year)
    try:
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
>>>>>>> Stashed changes
    
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
    
    # Get annual report from StudentMonthlyStatus
    annual_report = DraftPayment.get_annual_report(selected_year)
    
    return render(request, 'analyze.html', {
        'monthly_totals': monthly_totals,
        'yearly_total_payments': yearly_total_payments,
        'yearly_total_expenses': yearly_total_expenses,
        'yearly_net': yearly_net,
        'confirmed_payments': confirmed_payments,
        'confirmed_expenses': confirmed_expenses,
        'annual_report': annual_report,
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
            fixed_fee=fixed_fee
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
        student.fixed_fee = request.POST.get('monthly_fee')
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
    search_query = request.GET.get('search_name', '').strip()
    student = None
    last_paid_month = None
    current_month_status = None
    selected_year = datetime.now().year
    
    if search_query:
        try:
<<<<<<< Updated upstream
            student = Student.objects.filter(name__icontains=search_query).first()
        except Exception:
=======
            student = Student.objects.get(name=search_query)
            # Get last paid month
            last_paid_month = DraftPayment.get_last_paid_month(student)
            
            # Get current month status
            current_month = datetime.now().month
            current_year = datetime.now().year
            try:
                current_month_status = StudentMonthlyStatus.objects.get(
                    student=student, month=current_month, year=current_year
                )
            except StudentMonthlyStatus.DoesNotExist:
                current_month_status = None
        except Student.DoesNotExist:
>>>>>>> Stashed changes
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
        statuses = StudentMonthlyStatus.objects.filter(student=student, year=year)
        status_by_month = {s.month: s for s in statuses}

        for month in range(1, 13):
            s = status_by_month.get(month)
            months.append({
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'status': s.status if s else 'Unpaid',
                'paid_amount': s.paid_amount if s else 0,
            })

    return render(request, 'partials/student_annual_report.html', {
        'student': student,
        'year': year,
        'months': months,
    })

def logout_view(request):
    logout(request)
    return redirect('index')
