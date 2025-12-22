from django.shortcuts import render, redirect
from .models import DraftPayment, DraftExpense

def index(request):
    return render(request, 'home.html')

def add_payment(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        amount = request.POST.get('amount')
        payment_type = request.POST.get('payment_type')
        description = request.POST.get('description')
        DraftPayment.objects.create(
            student_name=student_name,
            amount=amount,
            payment_type=payment_type,
            description=description
        )
        if request.headers.get('HX-Request'):
            return render(request, 'home.html')
        return redirect('index')
    return render(request, 'add_payment.html')

def add_expense(request):
    if request.method == 'POST':
        expense_name = request.POST.get('expense_name')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        description = request.POST.get('description')
        DraftExpense.objects.create(
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

def login_view(request):
    # Placeholder login view
    return render(request, 'home.html')
