from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from functools import wraps
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from datetime import datetime, timedelta
from accounts.models import CustomUser
from .models import Customer, InventoryItem, Expense, Payment, BillClaim, Sale, SaleItem, SalePayment, LedgerEntry
from django.core.paginator import Paginator
from .forms import CustomerForm, InventoryItemForm, ExpenseForm, PaymentForm, BillClaimForm, SaleForm, SaleItemForm, CombinedSaleItemForm, SalePaymentForm
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

def is_manager(user):
    return user.is_superuser or (user.is_authenticated and user.is_manager)

# Custom decorator: redirect unauthenticated to login, raise 403 for authenticated non-managers
def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url='/login/')
        if not is_manager(user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


@login_required
def dashboard(request):
    """Dashboard with key metrics"""
    context = {
        'total_employees': CustomUser.objects.filter(status='active').count(),
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


# Customer Views
@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    qs = Customer.objects.all()
    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(customer_id__icontains=query) |
            Q(company__icontains=query) |
            Q(phone__icontains=query)
        )
    if status_filter:
        qs = qs.filter(status=status_filter)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/customer_list.html', {
        'customers': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
    })


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
    qs = InventoryItem.objects.all()
    if query:
        qs = qs.filter(
            Q(part_name__icontains=query) |
            Q(part_code__icontains=query) |
            Q(category__icontains=query)
        )
    if category_filter:
        qs = qs.filter(category__icontains=category_filter)
    if low_stock:
        qs = qs.filter(quantity__lte=F('minimum_stock'))
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/inventory_list.html', {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'category_filter': category_filter,
        'low_stock': low_stock,
    })


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
    qs = Expense.objects.all()
    if query:
        qs = qs.filter(
            Q(description__icontains=query) |
            Q(paid_to__icontains=query) |
            Q(receipt_number__icontains=query)
        )
    if category_filter:
        qs = qs.filter(category=category_filter)
    if month_filter:
        try:
            month, year = month_filter.split('-')
            qs = qs.filter(date__month=int(month), date__year=int(year))
        except Exception:
            pass
    total_expenses = qs.aggregate(total=Sum('amount'))['total'] or 0
    credit_total = LedgerEntry.objects.filter(entry_type='credit').aggregate(total=Sum('amount'))['total'] or 0
    debit_total = LedgerEntry.objects.filter(entry_type='debit').aggregate(total=Sum('amount'))['total'] or 0
    current_balance = (credit_total or 0) - (debit_total or 0)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/expense_list.html', {
        'expenses': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'category_filter': category_filter,
        'month_filter': month_filter,
        'total_expenses': total_expenses,
        'balance': current_balance,
    })


@login_required
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            exp = form.save()  # Ledger entry now created exclusively by post_save signal
            messages.success(request, 'Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'core/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
@manager_required
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
@manager_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expense_list')
    return render(request, 'core/confirm_delete.html', {'object': expense, 'type': 'Expense'})


@login_required
def expense_detail(request, pk):
    """View expense details"""
    expense = get_object_or_404(Expense, pk=pk)
    
    # Check if this expense was created from a bill claim
    related_claim = None
    related_claim_submitter = None
    related_claim_approver = None
    related_claim_approval_date = None
    try:
        related_claim = BillClaim.objects.get(expense=expense)
    except BillClaim.DoesNotExist:
        pass
    else:
        submitter_name = related_claim.submitter.get_full_name().strip()
        if not submitter_name:
            submitter_name = related_claim.submitter.username
        related_claim_submitter = submitter_name

        if related_claim.approved_by:
            approver_name = related_claim.approved_by.get_full_name().strip()
            if not approver_name:
                approver_name = related_claim.approved_by.username
            related_claim_approver = approver_name
        related_claim_approval_date = related_claim.approval_date
    
    context = {
        'expense': expense,
        'related_claim': related_claim,
        'related_claim_submitter': related_claim_submitter,
        'related_claim_approver': related_claim_approver,
        'related_claim_approval_date': related_claim_approval_date,
        'title': 'Expense Details'
    }
    return render(request, 'core/expense_detail.html', context)


# Payment Views
@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    payment_type = request.GET.get('payment_type', '')
    qs = Payment.objects.all()
    if query:
        qs = qs.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__customer_id__icontains=query)
        )
    if status_filter:
        qs = qs.filter(status=status_filter)
    if payment_type:
        qs = qs.filter(payment_type=payment_type)
    total_pending = qs.filter(status__in=['pending', 'overdue']).aggregate(
        total=Sum(F('total_amount') - F('paid_amount'))
    )['total'] or 0
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/payment_list.html', {
        'payments': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'payment_type': payment_type,
        'total_pending': total_pending
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
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
@user_passes_test(lambda u: u.is_superuser)
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
@user_passes_test(lambda u: u.is_superuser)
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('payment_list')
    return render(request, 'core/confirm_delete.html', {'object': payment, 'type': 'Payment'})


# Bill Claim Views
@login_required
def submit_bill_claim(request):
    """Employee submits a new bill claim"""
    if request.method == 'POST':
        form = BillClaimForm(request.POST, request.FILES)
        if form.is_valid():
            bill_claim = form.save(commit=False)
            bill_claim.submitter = request.user
            bill_claim.status = 'pending'
            bill_claim.save()
            messages.success(request, 'Bill claim submitted successfully!')
            return redirect('my_bill_claims')
    else:
        form = BillClaimForm()

    return render(request, 'core/bill_claim_form.html', {'form': form, 'title': 'Submit Bill Claim'})


@login_required
def my_bill_claims(request):
    """Employee views their own submitted claims"""
    status_filter = request.GET.get('status', '')
    bill_claims = BillClaim.objects.filter(submitter=request.user).order_by('-created_at')

    if status_filter:
        bill_claims = bill_claims.filter(status=status_filter)

    context = {
        'bill_claims': bill_claims,
        'status_filter': status_filter,
        'title': 'My Bill Claims',
        'is_manager_view': False,
    }
    return render(request, 'core/bill_claim_list.html', context)


@login_required
@manager_required
def list_bill_claims(request):
    """Manager views all claims from all employees"""
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '')
    
    bill_claims = BillClaim.objects.all().order_by('-created_at')

    if status_filter:
        bill_claims = bill_claims.filter(status=status_filter)
    
    if query:
        bill_claims = bill_claims.filter(
            Q(submitter__username__icontains=query) |
            Q(submitter__first_name__icontains=query) |
            Q(submitter__last_name__icontains=query) |
            Q(description__icontains=query)
        )

    # Calculate totals
    total_pending = bill_claims.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_approved = bill_claims.filter(status='approved').aggregate(total=Sum('amount'))['total'] or 0
    total_rejected = bill_claims.filter(status='rejected').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'bill_claims': bill_claims,
        'status_filter': status_filter,
        'query': query,
        'title': 'All Bill Claims',
        'is_manager_view': True,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
    }
    return render(request, 'core/bill_claim_list.html', context)


@login_required
@manager_required
def approve_bill_claim(request, pk):
    """Manager approves a bill claim and creates expense"""
    bill_claim = get_object_or_404(BillClaim, pk=pk)
    
    if bill_claim.status != 'pending':
        messages.warning(request, 'This claim has already been processed.')
        return redirect('list_bill_claims')

    if request.method == 'POST':
        from django.utils import timezone
        
        bill_claim.status = 'approved'
        bill_claim.approved_by = request.user
        bill_claim.approval_date = timezone.now().date()
        
        # Get employee name (fallback to username if no full name)
        employee_name = bill_claim.submitter.get_full_name().strip()
        if not employee_name:
            employee_name = bill_claim.submitter.username
        
        # Create a new Expense entry
        expense = Expense.objects.create(
            date=bill_claim.bill_date,
            category='other',
            description=f"Bill Claim by {employee_name}: {bill_claim.description}",
            amount=bill_claim.amount,
            paid_to=employee_name,
            payment_method='bank_transfer',
            notes=f"Approved bill claim (ID: {bill_claim.pk})",
        )
        bill_claim.expense = expense
        bill_claim.save()
        
        messages.success(request, f'Bill claim approved and expense created! Amount: ${bill_claim.amount}')
        return redirect('list_bill_claims')

    context = {
        'bill_claim': bill_claim,
        'title': 'Approve Bill Claim',
        'action': 'approve',
    }
    return render(request, 'core/bill_claim_review.html', context)


@login_required
@manager_required
def reject_bill_claim(request, pk):
    """Manager rejects a bill claim"""
    bill_claim = get_object_or_404(BillClaim, pk=pk)
    
    if bill_claim.status != 'pending':
        messages.warning(request, 'This claim has already been processed.')
        return redirect('list_bill_claims')

    if request.method == 'POST':
        from django.utils import timezone
        
        bill_claim.status = 'rejected'
        bill_claim.approved_by = request.user
        bill_claim.approval_date = timezone.now().date()
        bill_claim.save()
        
        messages.warning(request, f'Bill claim rejected for {bill_claim.submitter.get_full_name()}.')
        return redirect('list_bill_claims')

    context = {
        'bill_claim': bill_claim,
        'title': 'Reject Bill Claim',
        'action': 'reject',
    }
    return render(request, 'core/bill_claim_review.html', context)


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
    
    # Current balance from ledger
    credit_total = LedgerEntry.objects.filter(entry_type='credit').aggregate(total=Sum('amount'))['total'] or 0
    debit_total = LedgerEntry.objects.filter(entry_type='debit').aggregate(total=Sum('amount'))['total'] or 0
    current_balance = (credit_total or 0) - (debit_total or 0)

    context = {
        'monthly_expenses': monthly_expenses,
        'payment_stats': payment_stats,
        'balance': current_balance,
    }
    return render(request, 'core/reports.html', context)


@login_required
@manager_required
def ledger(request):
    """Simple ledger listing showing credits and debits with current balance."""
    qs = LedgerEntry.objects.all().order_by('-timestamp')
    credit_total = qs.filter(entry_type='credit').aggregate(total=Sum('amount'))['total'] or 0
    debit_total = qs.filter(entry_type='debit').aggregate(total=Sum('amount'))['total'] or 0
    current_balance = (credit_total or 0) - (debit_total or 0)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'entries': page_obj.object_list,
        'page_obj': page_obj,
        'balance': current_balance,
        'credit_total': credit_total,
        'debit_total': debit_total,
    }
    return render(request, 'core/ledger.html', context)


@login_required
def export_excel(request):
    """Export all data to Excel"""
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Export Employees
    ws_employees = wb.create_sheet("Employees")
    ws_employees.append(['ID', 'Name', 'Position', 'Department', 'Salary', 'Status', 'Join Date'])
    for emp in CustomUser.objects.all():
        ws_employees.append([
            emp.employee_id, emp.get_full_name(), emp.position, emp.department, 
            float(emp.salary) if emp.salary else 0, emp.status, emp.join_date
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


# =========================
# Sales Views (minimal UI)
# =========================

from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('core.view_sale', raise_exception=True)
def sale_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    qs = Sale.objects.select_related('customer').all().order_by('-created_at')
    if query:
        qs = qs.filter(
            Q(sale_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__customer_id__icontains=query)
        )
    if status:
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    # Sales overview metrics
    # Business rule: exclude Draft & Quotation from aggregate totals and dues
    totals_qs = qs.exclude(status__in=['draft', 'quote'])  # after filters
    total_sales_amount = totals_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid_amount = (
        totals_qs.annotate(paid=Sum('payments__amount')).aggregate(total=Sum('paid'))['total'] or 0
    )
    total_due_amount = (total_sales_amount or 0) - (total_paid_amount or 0)
    return render(request, 'core/sale_list.html', {
        'sales': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'total_sales_amount': total_sales_amount,
        'total_paid_amount': total_paid_amount,
        'total_due_amount': total_due_amount,
    })


@login_required
@permission_required('core.add_sale', raise_exception=True)
def sale_create(request):
    """Create a sale and first item on the same page.
    For inventory item type, unit price is forced from selected inventory item.
    For machine item type, accept machine_name + description.
    """
    if request.method == 'POST':
        sale_form = SaleForm(request.POST)
        item_form = CombinedSaleItemForm(request.POST)
        if sale_form.is_valid() and item_form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                sale = sale_form.save(commit=False)
                sale.created_by = request.user
                sale.save()

                cd = item_form.cleaned_data
                if cd['item_type'] == 'inventory':
                    inv = cd['inventory_item']
                    unit_price = inv.unit_price
                    desc = f"{inv.part_name} ({inv.part_code})"
                    SaleItem.objects.create(
                        sale=sale,
                        item_type='inventory',
                        inventory_item=inv,
                        description=desc,
                        quantity=cd['quantity'],
                        unit_price=unit_price,
                    )
                else:
                    # machine: merge name + description into one description field
                    machine_label = cd.get('machine_name') or ''
                    desc = f"{machine_label} - {cd.get('description') or ''}".strip(' -')
                    SaleItem.objects.create(
                        sale=sale,
                        item_type='non_inventory',
                        inventory_item=None,
                        description=desc,
                        quantity=cd['quantity'],
                        unit_price=cd['unit_price'],
                    )
            messages.success(request, 'Sale created with first item. You can add more items if needed.')
            return redirect('sale_detail', pk=sale.pk)
        else:
            # Bubble up form errors to messages
            for f in (sale_form, item_form):
                for field, errs in f.errors.items():
                    for err in errs:
                        messages.error(request, f"{field}: {err}")
    else:
        sale_form = SaleForm()
        item_form = CombinedSaleItemForm()
    # Provide inventory prices for client-side autofill
    inv_qs = None
    try:
        inv_qs = item_form.fields['inventory_item'].queryset
    except Exception:
        inv_qs = InventoryItem.objects.none()
    inventory_prices = {str(i.id): float(i.unit_price) for i in inv_qs}
    return render(request, 'core/sale_form.html', {
        'form': sale_form,
        'item_form': item_form,
        'title': 'Create Sale',
        'inventory_prices': inventory_prices,
    })


@login_required
@permission_required('core.add_sale', raise_exception=True)
def sale_quote_create(request):
    """Create a quotation (dummy sale) that doesn't affect stock/balance until converted."""
    if request.method == 'POST':
        sale_form = SaleForm(request.POST)
        item_form = CombinedSaleItemForm(request.POST)
        if sale_form.is_valid() and item_form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                sale = sale_form.save(commit=False)
                sale.created_by = request.user
                sale.status = 'quote'
                sale.save()

                cd = item_form.cleaned_data
                if cd['item_type'] == 'inventory':
                    inv = cd['inventory_item']
                    unit_price = inv.unit_price
                    desc = f"{inv.part_name} ({inv.part_code})"
                    SaleItem.objects.create(
                        sale=sale,
                        item_type='inventory',
                        inventory_item=inv,
                        description=desc,
                        quantity=cd['quantity'],
                        unit_price=unit_price,
                    )
                else:
                    machine_label = cd.get('machine_name') or ''
                    desc = f"{machine_label} - {cd.get('description') or ''}".strip(' -')
                    SaleItem.objects.create(
                        sale=sale,
                        item_type='non_inventory',
                        inventory_item=None,
                        description=desc,
                        quantity=cd['quantity'],
                        unit_price=cd['unit_price'],
                    )
            messages.success(request, 'Quotation created. Convert to invoice when ready.')
            return redirect('sale_detail', pk=sale.pk)
        else:
            for f in (sale_form, item_form):
                for field, errs in f.errors.items():
                    for err in errs:
                        messages.error(request, f"{field}: {err}")
    else:
        sale_form = SaleForm()
        item_form = CombinedSaleItemForm()
    inv_qs = None
    try:
        inv_qs = item_form.fields['inventory_item'].queryset
    except Exception:
        inv_qs = InventoryItem.objects.none()
    inventory_prices = {str(i.id): float(i.unit_price) for i in inv_qs}
    return render(request, 'core/sale_form.html', {
        'form': sale_form,
        'item_form': item_form,
        'title': 'Create Quotation',
        'inventory_prices': inventory_prices,
        'is_quote': True,
    })


@login_required
@permission_required('core.change_sale', raise_exception=True)
def sale_convert_to_invoice(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status != 'quote':
        messages.info(request, 'This sale is not a quotation.')
        return redirect('sale_detail', pk=sale.pk)
    sale.status = 'draft'
    sale.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Quotation converted to invoice. You can now finalize when ready.')
    return redirect('sale_detail', pk=sale.pk)


@login_required
@permission_required('core.view_sale', raise_exception=True)
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('customer'), pk=pk)
    items = sale.items.select_related('inventory_item').all()
    payments = sale.payments.all()
    add_item_form = None
    add_payment_form = None
    if request.user.has_perm('core.add_saleitem') and sale.status == 'draft':
        add_item_form = SaleItemForm()
    if request.user.has_perm('core.add_salepayment') and sale.status != 'cancelled' and sale.status != 'quote':
        add_payment_form = SalePaymentForm()
    # Inventory prices for client-side autofill in add-item form
    inv_qs = None
    if add_item_form:
        try:
            inv_qs = add_item_form.fields['inventory_item'].queryset
        except Exception:
            inv_qs = InventoryItem.objects.none()
    inventory_prices = {str(i.id): float(i.unit_price) for i in (inv_qs or [])}
    context = {
        'sale': sale,
        'items': items,
        'payments': payments,
        'add_item_form': add_item_form,
        'add_payment_form': add_payment_form,
        'inventory_prices': inventory_prices,
    }
    return render(request, 'core/sale_detail.html', context)


@login_required
@permission_required('core.view_sale', raise_exception=True)
def sale_invoice(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('customer'), pk=pk)
    items = sale.items.select_related('inventory_item').all()
    context = {
        'sale': sale,
        'items': items,
    }
    return render(request, 'core/sale_invoice.html', context)


@login_required
@permission_required('core.add_saleitem', raise_exception=True)
def sale_add_item(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status != 'draft':
        messages.warning(request, 'Cannot add items to a finalized sale.')
        return redirect('sale_detail', pk=sale.pk)
    if request.method == 'POST':
        form = SaleItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.sale = sale
            # Basic validation: require description for non-inventory items
            if item.item_type == 'non_inventory' and not item.description:
                messages.error(request, 'Description is required for non-inventory items.')
            else:
                # If inventory item selected, force unit price from inventory
                if item.item_type == 'inventory' and item.inventory_item:
                    item.unit_price = item.inventory_item.unit_price
                item.save()
                messages.success(request, 'Item added to sale.')
                return redirect('sale_detail', pk=sale.pk)
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
    return redirect('sale_detail', pk=sale.pk)


@login_required
@permission_required('core.finalize_sale', raise_exception=True)
def sale_finalize(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status == 'finalized':
        messages.info(request, 'Sale already finalized.')
        return redirect('sale_detail', pk=sale.pk)
    try:
        low_stock = sale.finalize(user=request.user)
        if low_stock:
            names = ', '.join([f"{i.part_name} ({i.part_code})" for i in low_stock])
            messages.warning(request, f"Finalized. Low stock: {names}")
        else:
            messages.success(request, 'Sale finalized successfully.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('sale_detail', pk=sale.pk)


@login_required
@permission_required('core.delete_saleitem', raise_exception=True)
def sale_delete_item(request, pk, item_pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status != 'draft':
        messages.warning(request, 'Cannot delete items from a finalized sale.')
        return redirect('sale_detail', pk=sale.pk)
    item = get_object_or_404(SaleItem, pk=item_pk, sale=sale)
    if request.method == 'POST':
        item.delete()
        try:
            sale.recalc_total(save=True)
        except Exception:
            pass
        messages.success(request, 'Item removed from sale.')
    return redirect('sale_detail', pk=sale.pk)


@login_required
@permission_required('core.view_salepayment', raise_exception=True)
def sale_payments_export(request, pk):
    import csv
    from django.utils.encoding import smart_str
    sale = get_object_or_404(Sale, pk=pk)
    payments = sale.payments.all().order_by('-payment_date', '-created_at')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{sale.sale_number}_payments.csv"'
    writer = csv.writer(response)
    writer.writerow(['Receipt', 'Date', 'Method', 'Amount'])
    for p in payments:
        writer.writerow([
            smart_str(p.receipt_number),
            p.payment_date,
            smart_str(p.get_method_display()),
            f"{p.amount}",
        ])
    return response


@login_required
@permission_required('core.add_salepayment', raise_exception=True)
def sale_add_payment(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status == 'cancelled':
        messages.warning(request, 'Cannot record payments for a cancelled sale.')
        return redirect('sale_detail', pk=sale.pk)

    if request.method == 'POST':
        form = SalePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.sale = sale
            # Prevent overpayment beyond balance due
            if payment.amount <= 0:
                messages.error(request, 'Amount must be greater than zero.')
            elif payment.amount > sale.balance_due:
                messages.error(request, 'Payment exceeds remaining balance.')
            else:
                payment.save()
                # Log to ledger as a credit (inflow)
                try:
                    LedgerEntry.objects.create(
                        entry_type='credit',
                        source='sale_payment',
                        reference=payment.receipt_number,
                        description=f"Payment for {sale.sale_number}",
                        amount=payment.amount,
                    )
                except Exception:
                    # Non-blocking on ledger write failure
                    pass
                messages.success(request, f'Payment recorded. Receipt: {payment.receipt_number}')
                return redirect('sale_detail', pk=sale.pk)
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
    return redirect('sale_detail', pk=sale.pk)


@login_required
@permission_required('core.view_salepayment', raise_exception=True)
def sale_payment_receipt(request, sale_pk, payment_pk):
    sale = get_object_or_404(Sale, pk=sale_pk)
    payment = get_object_or_404(SalePayment, pk=payment_pk, sale=sale)
    context = {
        'sale': sale,
        'payment': payment,
    }
    return render(request, 'core/sale_payment_receipt.html', context)

