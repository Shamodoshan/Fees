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
        payment_type = request.POST.get('payment_type')
        description = request.POST.get('description')
        DraftPayment.objects.create(
            user=request.user,
            student_name=student_name,
            amount=amount,
            payment_type=payment_type,
            description=description
        )
        if request.headers.get('HX-Request'):
            return render(request, 'home.html')
        return redirect('index')
    return render(request, 'add_payment.html')

@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        expense_name = request.POST.get('expense_name')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        description = request.POST.get('description')
        DraftExpense.objects.create(
            user=request.user,
            expense_name=expense_name,
            amount=amount,
            category=category,
            description=description
        )
        if request.headers.get('HX-Request'):
            return render(request, 'home.html')
        return redirect('index')
    return render(request, 'add_expense.html')

def view_payments(request):
    payments = DraftPayment.objects.all().order_by('-created_at')
    return render(request, 'view_payments.html', {
        'payments': payments
    })

def view_expenses(request):
    expenses = DraftExpense.objects.all().order_by('-created_at')
    return render(request, 'view_expenses.html', {
        'expenses': expenses
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
