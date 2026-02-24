import logging

from django.db import models, transaction
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
import uuid
from django.conf import settings

# --- Product Model ---
class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    sale_unit = models.CharField(max_length=20, choices=[('pcs', 'Pieces'), ('kg', 'Kilogram'), ('ltr', 'Liter'), ('mtr', 'Meter')], default='pcs')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return f"{self.name} ({self.sale_unit})"
import logging

from django.db import models, transaction
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
import uuid
from django.conf import settings

logger = logging.getLogger(__name__)

# Allowed file extensions for bill claim attachments
ALLOWED_ATTACHMENT_EXTENSIONS = [
    'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',
    'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt',
]


class CustomerIdSequence(models.Model):
    """Singleton sequence tracker for continuous customer serials.
    Holds the last assigned serial to ensure concurrency-safe increments.
    """
    last_serial = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"CustomerIdSequence(last_serial={self.last_serial})"

    class Meta:
        verbose_name = "Customer ID Sequence"
        verbose_name_plural = "Customer ID Sequences"


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
        # Auto-generate only if missing
        if not self.customer_id:
            from django.utils import timezone
            today = timezone.now().date()
            formatted_date = today.strftime('%d%m%Y')  # DDMMYYYY
            # Obtain/lock sequence row
            with transaction.atomic():
                seq, _created = CustomerIdSequence.objects.select_for_update().get_or_create(pk=1, defaults={'last_serial': 0})
                seq.last_serial += 1
                serial = seq.last_serial
                seq.save(update_fields=['last_serial'])
            self.customer_id = f"FE{formatted_date}-{serial:02d}"  # zero-padded serial
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
    INVENTORY_TYPE_CHOICES = [
        ('box', 'Box'),
        ('piece', 'Piece'),
        ('drum', 'Drum'),
        ('batch', 'Batch'),
        ('loose', 'Loose'),
    ]
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='inventory_items', null=True, blank=True)
    inventory_type = models.CharField(max_length=20, choices=INVENTORY_TYPE_CHOICES, default='box')
    identifier = models.CharField(max_length=50, blank=True, help_text="Box/Drum/Batch No")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    purchase_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    remaining_quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    status = models.CharField(max_length=20, default='in_stock')

    def save(self, *args, **kwargs):
        # Set remaining_quantity to quantity if not set
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity
        # Always default status to 'in_stock' if not set
        if not self.status:
            self.status = 'in_stock'
        super().save(*args, **kwargs)
    location = models.CharField(max_length=100, blank=True, help_text="Warehouse location/shelf")
    supplier = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['product', 'identifier', 'created_at']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
    
    def __str__(self):
        product_name = self.product.name if self.product else "(No Product)"
        return f"{product_name} [{self.identifier}] ({self.quantity} {self.unit})"
    
    @property
    def total_value(self):
        from decimal import Decimal
        if self.quantity is None or self.purchase_price_per_unit is None:
            return Decimal('0.00')
        return self.quantity * self.purchase_price_per_unit

    @property
    def is_low_stock(self):
        """Return True when remaining stock is considered low.

        Priority:
        - If an integer `minimum_stock` field exists on the model, compare against that.
        - Otherwise, use a default heuristic: remaining_quantity <= 10% of original quantity.
        """
        from decimal import Decimal, InvalidOperation
        try:
            if self.remaining_quantity is None:
                return False
            rq = Decimal(str(self.remaining_quantity))
            qty = Decimal(str(self.quantity or 0))
            # If model has minimum_stock field, prefer it
            if hasattr(self, 'minimum_stock') and self.minimum_stock is not None:
                try:
                    return rq <= Decimal(str(self.minimum_stock))
                except (InvalidOperation, TypeError):
                    pass
            if qty == 0:
                return rq <= 0
            return rq <= (Decimal('0.1') * qty)
        except (InvalidOperation, TypeError):
            return False
    

    @property
    def stock_status(self):
        from decimal import Decimal
        if self.remaining_quantity is None or self.quantity is None:
            return "In Stock"
        rq = Decimal(str(self.remaining_quantity))
        qty = Decimal(str(self.quantity))
        if rq == 0:
            return "Out of Stock"
        elif rq <= Decimal('0.1') * qty:
            return "Low Stock"
        return "In Stock"


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
        ("quote", "Quotation"),
        ("draft", "Draft"),
        ("finalized", "Finalized"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, related_name='sales')
    sale_number = models.CharField(max_length=100, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
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
                # Deduct from all available boxes for the product
                product = item.inventory_item.product
                required_qty = item.quantity
                available_boxes = InventoryItem.objects.filter(product=product, quantity__gt=0).order_by('created_at')
                total_available = sum([box.quantity for box in available_boxes])
                if total_available < required_qty:
                    pname = product.name if product else "(No Product)"
                    raise ValueError(f"Insufficient stock for {pname}. Available: {total_available}, required: {required_qty}")
                for box in available_boxes:
                    if required_qty <= 0:
                        break
                    deduct = min(box.quantity, required_qty)
                    previous = box.quantity
                    box.quantity = previous - deduct
                    # Also update remaining_quantity if used
                    if hasattr(box, 'remaining_quantity') and box.remaining_quantity is not None:
                        box.remaining_quantity = box.remaining_quantity - deduct
                    box.save(update_fields=['quantity', 'remaining_quantity', 'updated_at'])
                    StockHistory.objects.create(
                        item=box,
                        transaction_type='out',
                        quantity=deduct,
                        previous_quantity=previous,
                        new_quantity=box.quantity,
                        reason=f"Sale {self.sale_number}",
                        created_by=(getattr(user, 'username', '') or '')
                    )
                    if box.is_low_stock:
                        low_stock_items.append(box)
                    required_qty -= deduct

        self.status = 'finalized'
        self.finalized_at = timezone.now()
        if user is not None:
            self.finalized_by = user
        self.save(update_fields=['status', 'finalized_at', 'finalized_by', 'updated_at'])
        return low_stock_items


class SaleItem(models.Model):
    """Line items for a Sale, allowing inventory and non-inventory entries."""

    ITEM_TYPE_CHOICES = [
        ("inventory", "Inventory"),
        ("non_inventory", "Machine"),
    ]

    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    inventory_item = models.ForeignKey('InventoryItem', on_delete=models.PROTECT, null=True, blank=True, related_name='sale_items')
    description = models.TextField(blank=True, help_text="Required for non-inventory items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])  # For non-inventory items; inventory price comes from InventoryItem
    line_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    class Meta:
        verbose_name = 'Sale Item'
        verbose_name_plural = 'Sale Items'

    def __str__(self):
        label = self.inventory_item.product.name if (self.item_type == 'inventory' and self.inventory_item) else self.description
        return f"{label} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Auto-calc line total
        # For inventory items prefer the sale's unit_price when provided (selling price).
        # Fallback to the inventory item's purchase_price_per_unit when unit_price is zero/empty.
        price = 0
        try:
            if self.item_type == 'inventory' and self.inventory_item:
                if self.unit_price is not None and float(self.unit_price) > 0:
                    price = self.unit_price
                else:
                    price = self.inventory_item.purchase_price_per_unit or 0
            else:
                price = self.unit_price or 0
        except Exception:
            price = self.unit_price or (self.inventory_item.purchase_price_per_unit if self.inventory_item else 0) if True else 0
        self.line_total = price * (self.quantity or 0)
        super().save(*args, **kwargs)
        # Update parent sale total quickly
        if self.sale_id:
            try:
                self.sale.recalc_total(save=True)
            except Exception:
                logger.exception('Failed to recalc total for Sale id=%s', self.sale_id)


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
    attachment = models.FileField(
        upload_to='bill_attachments/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS)],
        help_text='Allowed: PDF, images, Office documents, CSV, TXT.',
    )
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


class LedgerEntry(models.Model):
    """Simple ledger to track credits (inflows) and debits (outflows).
    Used for calculating current balance and auditing payments/expenses.
    """

    ENTRY_TYPES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]

    SOURCES = [
        ("sale_payment", "Sale Payment"),
        ("expense", "Expense"),
        ("other", "Other"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    source = models.CharField(max_length=20, choices=SOURCES, default="other")
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.entry_type} {self.amount} ({self.source})"
