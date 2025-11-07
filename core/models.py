from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from django.conf import settings


class Customer(models.Model):
    """Customer Management Model"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=200)
    customer_id = models.CharField(max_length=50, unique=True, editable=False)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.name} ({self.customer_id})"


class InventoryItem(models.Model):
    """Inventory/Warehouse Management Model for Machine Parts"""
    UNIT_CHOICES = [
        ('pcs', 'Pieces'),
        ('box', 'Box'),
        ('kg', 'Kilogram'),
        ('ltr', 'Liter'),
        ('mtr', 'Meter'),
    ]
    
    part_name = models.CharField(max_length=200)
    part_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pcs')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=100, blank=True, help_text="Warehouse location/shelf")
    minimum_stock = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    supplier = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['part_name']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
    
    def __str__(self):
        return f"{self.part_name} ({self.part_code})"
    
    @property
    def total_value(self):
        return self.quantity * self.unit_price
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock


class Expense(models.Model):
    """Daily Expense Management Model"""
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('transport', 'Transport'),
        ('supplies', 'Supplies'),
        ('rent', 'Rent'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]
    
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_to = models.CharField(max_length=200, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True, help_text="Cash, Bank Transfer, etc.")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
    
    def __str__(self):
        return f"{self.category} - {self.amount} ({self.date})"


class Payment(models.Model):
    """Payment Management Model"""
    PAYMENT_TYPE_CHOICES = [
        ('down_payment', 'Down Payment'),
        ('installment', 'Installment'),
        ('full_payment', 'Full Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    invoice_number = models.CharField(max_length=100, unique=True, editable=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    payment_date = models.DateField()
    next_payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today = timezone.now()
            self.invoice_number = f"INV-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount
    
    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.total_amount


class Sale(models.Model):
    """Sales order/invoice core model (covers inventory and non-inventory sales).
    Minimal fields for initial review; totals can be recalculated from items.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("finalized", "Finalized"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, related_name='sales')
    sale_number = models.CharField(max_length=100, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    expected_installments = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_sales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='finalized_sales')

    # Stored total for quick filtering; recomputed via recalc_total() when needed
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'

    def __str__(self):
        return f"{self.sale_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            today = timezone.now()
            self.sale_number = f"S-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def recalc_total(self, save=True):
        total = sum((item.line_total for item in self.items.all()), start=0)
        # Ensure Decimal type consistency
        self.total_amount = total
        if save:
            super().save(update_fields=["total_amount", "updated_at"])

    @property
    def total_paid(self):
        agg = self.payments.aggregate(total=models.Sum('amount'))
        return agg['total'] or 0

    @property
    def balance_due(self):
        return (self.total_amount or 0) - (self.total_paid or 0)

    @transaction.atomic
    def finalize(self, user=None):
        """Finalize the sale by decrementing inventory for inventory items and logging stock history.
        Raises ValueError if already finalized or insufficient stock.
        Returns a list of items that are now low stock.
        """
        if self.status == 'finalized':
            raise ValueError("Sale already finalized")

        low_stock_items = []
        for item in self.items.select_related('inventory_item'):
            if item.item_type == 'inventory' and item.inventory_item:
                inv = item.inventory_item
                if inv.quantity < item.quantity:
                    raise ValueError(f"Insufficient stock for {inv.part_name} ({inv.part_code}). Available: {inv.quantity}, required: {item.quantity}")
                previous = inv.quantity
                inv.quantity = previous - item.quantity
                inv.save(update_fields=['quantity', 'updated_at'])

                StockHistory.objects.create(
                    item=inv,
                    transaction_type='out',
                    quantity=item.quantity,
                    previous_quantity=previous,
                    new_quantity=inv.quantity,
                    reason=f"Sale {self.sale_number}",
                    created_by=(getattr(user, 'username', '') or '')
                )

                if inv.is_low_stock:
                    low_stock_items.append(inv)

        self.status = 'finalized'
        self.finalized_at = timezone.now()
        if user is not None:
            self.finalized_by = user
        self.save(update_fields=['status', 'finalized_at', 'finalized_by', 'updated_at'])
        return low_stock_items


class SaleItem(models.Model):
    """Line items for a Sale, allowing inventory and non-inventory entries."""

    ITEM_TYPE_CHOICES = [
        ("inventory", "Inventory Item"),
        ("non_inventory", "Non-Inventory Item"),
    ]

    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    inventory_item = models.ForeignKey('InventoryItem', on_delete=models.PROTECT, null=True, blank=True, related_name='sale_items')
    description = models.CharField(max_length=255, blank=True, help_text="Required for non-inventory items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    line_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    class Meta:
        verbose_name = 'Sale Item'
        verbose_name_plural = 'Sale Items'

    def __str__(self):
        label = self.inventory_item.part_name if (self.item_type == 'inventory' and self.inventory_item) else self.description
        return f"{label} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Auto-calc line total
        self.line_total = (self.unit_price or 0) * (self.quantity or 0)
        super().save(*args, **kwargs)
        # Update parent sale total quickly
        if self.sale_id:
            try:
                self.sale.recalc_total(save=True)
            except Exception:
                # Avoid breaking saves due to total recompute; can be recalculated later
                pass


class SalePayment(models.Model):
    """Payments made against a Sale. Each generates a receipt number."""

    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    ]

    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='payments')
    receipt_number = models.CharField(max_length=100, unique=True, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=30, choices=METHOD_CHOICES, default='cash')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Sale Payment'
        verbose_name_plural = 'Sale Payments'

    def __str__(self):
        return f"{self.receipt_number} - {self.sale.sale_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            today = timezone.now()
            self.receipt_number = f"RCPT-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


class BillClaim(models.Model):
    """Model for Employee Bill Claims"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bill_claims')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField()
    bill_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attachment = models.FileField(upload_to='bill_attachments/', blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bill_claims')
    approval_date = models.DateField(null=True, blank=True)
    expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True, related_name='bill_claim')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bill Claim'
        verbose_name_plural = 'Bill Claims'

    def __str__(self):
        return f"Bill Claim by {self.submitter.username} - {self.amount} ({self.status})"


class StockHistory(models.Model):
    """Track inventory stock changes"""
    TRANSACTION_CHOICES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='stock_history')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock History'
        verbose_name_plural = 'Stock History'
    
    def __str__(self):
        return f"{self.item.part_name} - {self.transaction_type} ({self.quantity})"
