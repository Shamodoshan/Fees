# UPDATED VIEWS.PY - Key Changes for New Student Model

# Replace all StudentMonthlyStatus references with Student methods

# 1. Update get_next_payment_month_year function
def get_next_payment_month_year(student):
    """
    Get the next payment month and year for a student based on their last payment.
    If there's a half-paid month, return that month for completion.
    """
    last_paid = student.get_last_paid_month()
    
    if last_paid:
        year, month, data = last_paid
        
        # If last month was half paid, return same month for completion
        if data.get('status') == 'Half Paid':
            return year, month, data.get('amount', 0)
        
        # Return next month
        if month == 12:
            return year + 1, 1, 0
        else:
            return year, month + 1, 0
    else:
        # No payment history - return current month
        today = date.today()
        return today.year, today.month, 0

# 2. Update add_payment view logic
@login_required(login_url='login')
def add_payment(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        student_id = request.POST.get('student_id')
        amount = request.POST.get('amount')
        payment_monthly_fee = request.POST.get('monthly_fee')
        description = request.POST.get('description')
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        
        error_message = None
        
        try:
            # Get student
            if student_id:
                student = Student.objects.get(pk=student_id)
            else:
                student = Student.objects.get(name=student_name)
            
            # Check if payment already exists for this month
            current_status = student.get_monthly_status(year, month)
            if current_status.get('status') in ['Paid', 'Accepted']:
                error_message = f"Cannot create new payment for {month}/{year} - payment is already {current_status.get('status')}."
            else:
                # Create payment
                payment_amount = Decimal(amount)
                monthly_fee_amount = Decimal(payment_monthly_fee) if payment_monthly_fee else Decimal('0')
                
                # Calculate total paid after this payment
                current_paid = Decimal(current_status.get('amount', 0))
                total_paid = current_paid + payment_amount
                
                # Determine status
                if total_paid >= monthly_fee_amount:
                    status = 'Paid'
                    final_amount = monthly_fee_amount
                elif total_paid > 0:
                    status = 'Half Paid'
                    final_amount = total_paid
                else:
                    status = 'Unpaid'
                    final_amount = Decimal('0')
                
                # Update student's monthly status
                student.update_monthly_status(
                    year=year,
                    month=month,
                    amount_paid=payment_amount,
                    monthly_fee=monthly_fee_amount,
                    payment_status=status
                )
                
                # Create DraftPayment record
                DraftPayment.objects.create(
                    user=request.user,
                    student=student,
                    amount=payment_amount,
                    monthly_fee=payment_monthly_fee,
                    description=description,
                    month=month,
                    year=year,
                    status=status
                )
                
                if request.headers.get('HX-Request'):
                    response = render(request, 'add_payment.html')
                    response['HX-Trigger'] = 'showDraftToast'
                    return response
                return redirect('index')
                
        except Student.DoesNotExist:
            error_message = "Student not found. Please check the student name."
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
        
        if error_message:
            if request.headers.get('HX-Request'):
                return render(request, 'add_payment.html', {
                    'error_message': error_message
                })
            return render(request, 'add_payment.html', {
                'error_message': error_message
            })
    
    return render(request, 'add_payment.html')

# 3. Update student_annual_report view
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
        # Get payment history for the year
        payment_history = student.get_payment_history(limit_months=12)
        
        # Filter for the requested year
        for month_data in payment_history:
            if month_data['year'] == year:
                months.append({
                    'month': month_data['month'],
                    'month_name': datetime(year, month_data['month'], 1).strftime('%B'),
                    'status': month_data['status'],
                    'paid_amount': month_data['amount'],
                })
        
        # Sort by month
        months.sort(key=lambda x: x['month'])
    
    return render(request, 'partials/student_annual_report.html', {
        'student': student,
        'year': year,
        'months': months
    })

# 4. Update analyze_view for annual reports
@login_required(login_url='login')
def analyze_view(request):
    # Get selected year from query parameter or default to current year
    selected_year = request.GET.get('year')
    try:
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
    
    # Get annual report using new Student method
    annual_data = Student.get_annual_report(selected_year)
    
    # Prepare monthly totals
    monthly_totals = {}
    for month in range(1, 13):
        month_name = datetime(selected_year, month, 1).strftime('%B')
        monthly_totals[month] = {
            'month_name': month_name,
            'total_payments': 0,
            'total_expenses': 0,
            'net_amount': 0
        }
    
    # Fill with actual data
    for month_data in annual_data:
        month_num = month_data['month']
        if month_num in monthly_totals:
            monthly_totals[month_num].update({
                'total_payments': month_data['total_collected'] or 0,
                'total_students': month_data['total_students'],
                'paid_students': month_data['paid_students'],
                'half_paid_students': month_data['half_paid_students'],
                'unpaid_students': month_data['unpaid_students']
            })
    
    # Get expenses for the year
    confirmed_expenses = DraftExpense.objects.filter(
        status='Accepted',
        created_time__year=selected_year
    ).order_by('created_time')
    
    # Add expenses to monthly totals
    for expense in confirmed_expenses:
        month = expense.created_time.month
        if month in monthly_totals:
            monthly_totals[month]['total_expenses'] += float(expense.amount)
            monthly_totals[month]['net_amount'] = (
                monthly_totals[month]['total_payments'] - 
                monthly_totals[month]['total_expenses']
            )
    
    context = {
        'selected_year': selected_year,
        'monthly_totals': monthly_totals,
        'expenses': confirmed_expenses,
        'available_years': get_available_years()
    }
    
    return render(request, 'analyze.html', context)

# 5. Update get_student_details view
@login_required(login_url='login')
def get_student_details(request):
    student_name = request.POST.get('student_name', '').strip()
    
    if not student_name:
        return HttpResponse('')
    
    try:
        student = Student.objects.get(name__iexact=student_name)
        
        # Get next payment info
        next_year, next_month, remaining_fee = get_next_payment_month_year(student)
        
        # Get last paid month info
        last_paid = student.get_last_paid_month()
        last_paid_month = None
        if last_paid:
            last_paid_month = {
                'year': last_paid[0],
                'month': last_paid[1],
                'status': last_paid[2].get('status'),
                'amount': last_paid[2].get('amount')
            }
        
        return render(request, 'partials/student_details.html', {
            'student': student,
            'next_month': next_month,
            'next_year': next_year,
            'remaining_fee': remaining_fee,
            'last_paid_month': last_paid_month
        })
        
    except Student.DoesNotExist:
        return render(request, 'partials/student_details.html', {'error': True})
