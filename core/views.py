from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import DraftPayment, DraftExpense

from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def add_payment(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        DraftPayment.objects.create(
            user=request.user,
            student_name=student_name,
            amount=amount,
            description=description
        )
        if request.headers.get('HX-Request'):
            response = render(request, 'add_payment.html')
            response['HX-Trigger'] = 'showDraftToast'
            return response
        return redirect('index')
    return render(request, 'add_payment.html')

@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        expense_name = request.POST.get('expense_name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        DraftExpense.objects.create(
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

def view_payments(request):
    payments = DraftPayment.objects.filter(status='Pending').order_by('-created_at')
    return render(request, 'view_payments.html', {
        'payments': payments
    })

def view_expenses(request):
    expenses = DraftExpense.objects.filter(status='Pending').order_by('-created_at')
    return render(request, 'view_expenses.html', {
        'expenses': expenses
    })

# Admin Approval Views
@login_required(login_url='login')
def approve_payment(request, pk):
    if request.user.is_staff:
        payment = DraftPayment.objects.get(pk=pk)
        payment.status = 'Accepted'
        payment.save()
    return redirect('view_payments')

@login_required(login_url='login')
def decline_payment(request, pk):
    if request.user.is_staff:
        payment = DraftPayment.objects.get(pk=pk)
        payment.status = 'Declined'
        payment.save()
    return redirect('view_payments')

@login_required(login_url='login')
def approve_expense(request, pk):
    if request.user.is_staff:
        expense = DraftExpense.objects.get(pk=pk)
        expense.status = 'Accepted'
        expense.save()
    return redirect('view_expenses')

@login_required(login_url='login')
def decline_expense(request, pk):
    if request.user.is_staff:
        expense = DraftExpense.objects.get(pk=pk)
        expense.status = 'Declined'
        expense.save()
    return redirect('view_expenses')

@login_required(login_url='login')
def view_confirmed(request):
    payments = DraftPayment.objects.filter(status='Accepted').order_by('-created_at')
    expenses = DraftExpense.objects.filter(status='Accepted').order_by('-created_at')
    return render(request, 'confirmed_transactions.html', {
        'payments': payments,
        'expenses': expenses
    })

from django.db.models import Sum, functions
from datetime import datetime

@login_required(login_url='login')
def analyze_view(request):
    # Aggregate payments by month and year
    payment_stats = DraftPayment.objects.filter(status='Accepted').annotate(
        month=functions.TruncMonth('created_at')
    ).values('month').annotate(total=Sum('amount')).order_by('-month')

    # Aggregate expenses by month and year
    expense_stats = DraftExpense.objects.filter(status='Accepted').annotate(
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

def logout_view(request):
    logout(request)
    return redirect('index')
