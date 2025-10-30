from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import Employee, Customer, InventoryItem, Expense, Payment
from .forms import EmployeeForm, CustomerForm, InventoryItemForm, ExpenseForm, PaymentForm
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill


@login_required
def dashboard(request):
    """Dashboard with key metrics"""
    context = {
        'total_employees': Employee.objects.filter(status='active').count(),
        'total_customers': Customer.objects.filter(status='active').count(),
        'total_inventory_items': InventoryItem.objects.count(),
        'low_stock_items': InventoryItem.objects.filter(quantity__lte=F('minimum_stock')).count(),
        'total_inventory_value': InventoryItem.objects.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0,
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'overdue_payments': Payment.objects.filter(status='overdue').count(),
        'total_pending_amount': Payment.objects.filter(
            status__in=['pending', 'overdue']
        ).aggregate(
            total=Sum(F('total_amount') - F('paid_amount'))
        )['total'] or 0,
        'monthly_expenses': Expense.objects.filter(
            date__month=datetime.now().month,
            date__year=datetime.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'recent_expenses': Expense.objects.all()[:5],
        'recent_payments': Payment.objects.all()[:5],
        'low_stock_alerts': InventoryItem.objects.filter(
            quantity__lte=F('minimum_stock')
        )[:5],
    }
    return render(request, 'core/dashboard.html', context)


# Employee Views
@login_required
def employee_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    employees = Employee.objects.all()
    
    if query:
        employees = employees.filter(
            Q(name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query)
        )
    
    if status_filter:
        employees = employees.filter(status=status_filter)
    
    return render(request, 'core/employee_list.html', {'employees': employees, 'query': query})


@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee added successfully!')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'core/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully!')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'core/employee_form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully!')
        return redirect('employee_list')
    return render(request, 'core/confirm_delete.html', {'object': employee, 'type': 'Employee'})


# Customer Views
@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    customers = Customer.objects.all()
    
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(customer_id__icontains=query) |
            Q(company__icontains=query) |
            Q(phone__icontains=query)
        )
    
    if status_filter:
        customers = customers.filter(status=status_filter)
    
    return render(request, 'core/customer_list.html', {'customers': customers, 'query': query})


@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('customer_list')
    return render(request, 'core/confirm_delete.html', {'object': customer, 'type': 'Customer'})


# Inventory Views
@login_required
def inventory_list(request):
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    low_stock = request.GET.get('low_stock', '')
    
    items = InventoryItem.objects.all()
    
    if query:
        items = items.filter(
            Q(part_name__icontains=query) |
            Q(part_code__icontains=query) |
            Q(category__icontains=query)
        )
    
    if category_filter:
        items = items.filter(category__icontains=category_filter)
    
    if low_stock:
        items = items.filter(quantity__lte=F('minimum_stock'))
    
    return render(request, 'core/inventory_list.html', {'items': items, 'query': query})


@login_required
def inventory_add(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item added successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'core/inventory_form.html', {'form': form, 'title': 'Add Inventory Item'})


@login_required
def inventory_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item updated successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'core/inventory_form.html', {'form': form, 'title': 'Edit Inventory Item'})


@login_required
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Inventory item deleted successfully!')
        return redirect('inventory_list')
    return render(request, 'core/confirm_delete.html', {'object': item, 'type': 'Inventory Item'})


# Expense Views
@login_required
def expense_list(request):
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    month_filter = request.GET.get('month', '')
    
    expenses = Expense.objects.all()
    
    if query:
        expenses = expenses.filter(
            Q(description__icontains=query) |
            Q(paid_to__icontains=query) |
            Q(receipt_number__icontains=query)
        )
    
    if category_filter:
        expenses = expenses.filter(category=category_filter)
    
    if month_filter:
        try:
            month, year = month_filter.split('-')
            expenses = expenses.filter(date__month=int(month), date__year=int(year))
        except:
            pass
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'core/expense_list.html', {
        'expenses': expenses, 
        'query': query,
        'total_expenses': total_expenses
    })


@login_required
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'core/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'core/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expense_list')
    return render(request, 'core/confirm_delete.html', {'object': expense, 'type': 'Expense'})


# Payment Views
@login_required
def payment_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    payment_type = request.GET.get('payment_type', '')
    
    payments = Payment.objects.all()
    
    if query:
        payments = payments.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__customer_id__icontains=query)
        )
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    
    total_pending = payments.filter(status__in=['pending', 'overdue']).aggregate(
        total=Sum(F('total_amount') - F('paid_amount'))
    )['total'] or 0
    
    return render(request, 'core/payment_list.html', {
        'payments': payments, 
        'query': query,
        'total_pending': total_pending
    })


@login_required
def payment_add(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment added successfully!')
            return redirect('payment_list')
    else:
        form = PaymentForm()
    return render(request, 'core/payment_form.html', {'form': form, 'title': 'Add Payment'})


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('payment_list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'core/payment_form.html', {'form': form, 'title': 'Edit Payment'})


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('payment_list')
    return render(request, 'core/confirm_delete.html', {'object': payment, 'type': 'Payment'})


# Reports
@login_required
def reports(request):
    """Reports page with various statistics"""
    # Monthly expense breakdown
    monthly_expenses = Expense.objects.filter(
        date__year=datetime.now().year
    ).values('category').annotate(total=Sum('amount')).order_by('-total')
    
    # Payment statistics
    payment_stats = {
        'pending': Payment.objects.filter(status='pending').count(),
        'completed': Payment.objects.filter(status='completed').count(),
        'overdue': Payment.objects.filter(status='overdue').count(),
    }
    
    context = {
        'monthly_expenses': monthly_expenses,
        'payment_stats': payment_stats,
    }
    return render(request, 'core/reports.html', context)


@login_required
def export_excel(request):
    """Export all data to Excel"""
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Export Employees
    ws_employees = wb.create_sheet("Employees")
    ws_employees.append(['ID', 'Name', 'Position', 'Department', 'Salary', 'Status', 'Join Date'])
    for emp in Employee.objects.all():
        ws_employees.append([
            emp.employee_id, emp.name, emp.position, emp.department, 
            float(emp.salary), emp.status, emp.join_date
        ])
    
    # Export Customers
    ws_customers = wb.create_sheet("Customers")
    ws_customers.append(['ID', 'Name', 'Company', 'Phone', 'City', 'Status'])
    for cust in Customer.objects.all():
        ws_customers.append([
            cust.customer_id, cust.name, cust.company, cust.phone, cust.city, cust.status
        ])
    
    # Export Inventory
    ws_inventory = wb.create_sheet("Inventory")
    ws_inventory.append(['Part Code', 'Part Name', 'Category', 'Quantity', 'Unit Price', 'Total Value'])
    for item in InventoryItem.objects.all():
        ws_inventory.append([
            item.part_code, item.part_name, item.category, item.quantity, 
            float(item.unit_price), float(item.total_value)
        ])
    
    # Export Expenses
    ws_expenses = wb.create_sheet("Expenses")
    ws_expenses.append(['Date', 'Category', 'Description', 'Amount', 'Paid To'])
    for exp in Expense.objects.all():
        ws_expenses.append([
            exp.date, exp.category, exp.description, float(exp.amount), exp.paid_to
        ])
    
    # Export Payments
    ws_payments = wb.create_sheet("Payments")
    ws_payments.append(['Invoice', 'Customer', 'Type', 'Total Amount', 'Paid Amount', 'Remaining', 'Status'])
    for pay in Payment.objects.all():
        ws_payments.append([
            pay.invoice_number, pay.customer.name, pay.payment_type, 
            float(pay.total_amount), float(pay.paid_amount), 
            float(pay.remaining_amount), pay.status
        ])
    
    # Save to response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=org_management_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    
    return response
