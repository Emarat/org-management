from django.contrib import admin
from .models import Customer, InventoryItem, Expense, Payment, StockHistory, BillClaim


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'name', 'company', 'phone', 'city', 'status']
    list_filter = ['status', 'city']
    search_fields = ['name', 'customer_id', 'company', 'phone', 'email']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'customer_id', 'company')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address', 'city')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
    )


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['part_code', 'part_name', 'category', 'quantity', 'unit', 'unit_price', 'total_value', 'is_low_stock', 'location']
    list_filter = ['category', 'unit']
    search_fields = ['part_name', 'part_code', 'category', 'supplier']
    list_per_page = 20
    
    fieldsets = (
        ('Part Information', {
            'fields': ('part_name', 'part_code', 'category', 'description')
        }),
        ('Stock Details', {
            'fields': ('quantity', 'unit', 'unit_price', 'minimum_stock')
        }),
        ('Location & Supplier', {
            'fields': ('location', 'supplier')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def total_value(self, obj):
        return f"${obj.total_value:.2f}"
    total_value.short_description = 'Total Value'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'category', 'description', 'amount', 'paid_to', 'payment_method']
    list_filter = ['category', 'date', 'payment_method']
    search_fields = ['description', 'paid_to', 'receipt_number']
    date_hierarchy = 'date'
    list_per_page = 20
    
    fieldsets = (
        ('Date & Category', {
            'fields': ('date', 'category')
        }),
        ('Expense Details', {
            'fields': ('description', 'amount', 'paid_to')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'receipt_number')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'payment_type', 'total_amount', 'paid_amount', 'remaining_amount', 'status', 'payment_date', 'next_payment_date']
    list_filter = ['payment_type', 'status', 'payment_date']
    search_fields = ['invoice_number', 'customer__name', 'customer__customer_id']
    date_hierarchy = 'payment_date'
    list_per_page = 20
    
    fieldsets = (
        ('Customer & Invoice', {
            'fields': ('customer', 'invoice_number', 'description')
        }),
        ('Payment Details', {
            'fields': ('payment_type', 'total_amount', 'paid_amount', 'payment_method')
        }),
        ('Dates & Status', {
            'fields': ('payment_date', 'next_payment_date', 'status')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def remaining_amount(self, obj):
        return f"${obj.remaining_amount:.2f}"
    remaining_amount.short_description = 'Remaining'


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ['item', 'transaction_type', 'quantity', 'previous_quantity', 'new_quantity', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['item__part_name', 'item__part_code', 'reason']
    date_hierarchy = 'created_at'
    list_per_page = 20
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('item', 'transaction_type', 'quantity')
        }),
        ('Stock Levels', {
            'fields': ('previous_quantity', 'new_quantity')
        }),
        ('Additional Information', {
            'fields': ('reason', 'created_by', 'created_at')
        }),
    )


@admin.register(BillClaim)
class BillClaimAdmin(admin.ModelAdmin):
    list_display = ['submitter', 'amount', 'bill_date', 'status', 'approved_by', 'approval_date']
    list_filter = ['status', 'bill_date', 'submitter']
    search_fields = ['submitter__username', 'description']
    date_hierarchy = 'bill_date'
    list_per_page = 20
    readonly_fields = ['approved_by', 'approval_date', 'expense']

    fieldsets = (
        ('Claim Details', {
            'fields': ('submitter', 'amount', 'description', 'bill_date', 'attachment')
        }),
        ('Approval Status', {
            'fields': ('status', 'approved_by', 'approval_date', 'expense')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_manager:
            return qs
        # Employees can only see their own claims
        return qs.filter(submitter=request.user)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and obj.submitter != request.user:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and obj.submitter != request.user:
            return False
        return super().has_delete_permission(request, obj)


# Customize admin site
admin.site.site_header = "Organization Management System"
admin.site.site_title = "Org Management"
admin.site.index_title = "Welcome to Organization Management System"
