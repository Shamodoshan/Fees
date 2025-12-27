from django.shortcuts import render, redirect
import json
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Payment, Expense, Student

from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def index(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def add_payment(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name')
        amount = request.POST.get('amount')
        year = request.POST.get('year')
        month = request.POST.get('month')
        description = request.POST.get('description')
        
        student = None
        if student_id:
            try:
                # Extract numeric ID from STU-XXXX (case insensitive)
                stu_pk = student_id.upper().replace('STU-', '').lstrip('0')
                student = Student.objects.get(pk=stu_pk)
            except (Student.DoesNotExist, ValueError):
                pass

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

@login_required(login_url='login')
def get_student_details(request):
    student_name = request.GET.get('student_name', '').strip()
    try:
        # Search by name
        student = Student.objects.filter(name__icontains=student_name).first()
        return render(request, 'partials/student_details.html', {'student': student})
    except (ValueError):
        return render(request, 'partials/student_details.html', {'student': None})

@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        expense_name = request.POST.get('expense_name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        Expense.objects.create(
            user=request.user,
            expense_name=expense_name,
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
    payments = Payment.objects.filter(status='Pending').order_by('-created_at')
    return render(request, 'view_payments.html', {
        'payments': payments
    })

@login_required(login_url='login')
def view_expenses(request):
    expenses = Expense.objects.filter(status='Pending').order_by('-created_at')
    return render(request, 'view_expenses.html', {
        'expenses': expenses
    })

# Admin Approval Views
@login_required(login_url='login')
def approve_payment(request, pk):
    if request.user.is_staff:
        payment = Payment.objects.get(pk=pk)
        
        # Check if admin adjusted the amount
        if request.method == 'POST':
            adjusted_amount = request.POST.get('adjusted_amount')
            if adjusted_amount:
                payment.amount = adjusted_amount
        
        payment.status = 'Accepted'
        payment.save()
        
        # Increment student's last paid month if linked
        if payment.student:
            d = payment.student.last_paid_date
            # Simple month increment logic: Always normalize to the 1st
            if d.month == 12:
                new_date = d.replace(year=d.year + 1, month=1, day=1)
            else:
                new_date = d.replace(month=d.month + 1, day=1)
            payment.student.last_paid_date = new_date
            payment.student.save()
            
    return redirect('view_payments')

@login_required(login_url='login')
def decline_payment(request, pk):
    if request.user.is_staff:
        payment = Payment.objects.get(pk=pk)
        payment.status = 'Declined'
        payment.save()
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
        expense.save()
    return redirect('view_expenses')

@login_required(login_url='login')
def decline_expense(request, pk):
    if request.user.is_staff:
        expense = Expense.objects.get(pk=pk)
        expense.status = 'Declined'
        expense.save()
    return redirect('view_expenses')

@login_required(login_url='login')
def view_confirmed(request):
    payments = Payment.objects.filter(status='Accepted').order_by('-created_at')
    expenses = Expense.objects.filter(status='Accepted').order_by('-created_at')
    return render(request, 'confirmed_transactions.html', {
        'payments': payments,
        'expenses': expenses
    })

@login_required(login_url='login')
def view_confirmed_payments(request):
    payments = Payment.objects.filter(status='Accepted').order_by('-created_at')
    return render(request, 'confirmed_payments.html', {
        'payments': payments
    })

@login_required(login_url='login')
def view_confirmed_expenses(request):
    expenses = Expense.objects.filter(status='Accepted').order_by('-created_at')
    return render(request, 'confirmed_expenses.html', {
        'expenses': expenses
    })

from django.db.models import Sum, functions
from datetime import datetime

@login_required(login_url='login')
def analyze_view(request):
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
    
    for e in expense_stats:
        m_str = e['month'].strftime('%B %Y')
        if m_str in monthly_data:
            monthly_data[m_str]['expenses'] = e['total']
        else:
            monthly_data[m_str] = {'month_obj': e['month'], 'payments': 0, 'expenses': e['total']}

    # Calculate net and sort
    final_report = []
    for month, data in monthly_data.items():
        net = data['payments'] - data['expenses']
        final_report.append({
            'month': month,
            'month_obj': data['month_obj'],
            'payments': data['payments'],
            'expenses': data['expenses'],
            'net': net
        })
    
    final_report.sort(key=lambda x: x['month_obj'], reverse=True)

    return render(request, 'analyze.html', {
        'report': final_report
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
    students = Student.objects.all().order_by('id')
    return render(request, 'students.html', {'students': students})

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
            response = render(request, 'students.html', {'students': Student.objects.all().order_by('id')})
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
            response = render(request, 'students.html', {'students': Student.objects.all().order_by('id')})
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
    
    if search_query:
        try:
            student = Student.objects.filter(name__icontains=search_query).first()
        except Exception:
            pass
    
    return render(request, 'partials/search_student_results.html', {
        'student': student,
        'search_query': search_query
    })

def logout_view(request):
    logout(request)
    return redirect('index')
