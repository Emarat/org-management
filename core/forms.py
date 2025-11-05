from django import forms
from .models import Customer, InventoryItem, Expense, Payment, BillClaim, Sale, SaleItem
from django import forms


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'company', 'email', 'phone', 
                  'address', 'city', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['part_name', 'part_code', 'description', 'category', 'quantity', 
                  'unit', 'unit_price', 'location', 'minimum_stock', 'supplier', 'notes']
        widgets = {
            'part_name': forms.TextInput(attrs={'class': 'form-control'}),
            'part_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount', 'paid_to', 
                  'receipt_number', 'payment_method', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_to': forms.TextInput(attrs={'class': 'form-control'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['customer', 'payment_type', 'total_amount', 
                  'paid_amount', 'payment_date', 'next_payment_date', 'status', 
                  'payment_method', 'description', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BillClaimForm(forms.ModelForm):
    class Meta:
        model = BillClaim
        fields = ['amount', 'description', 'bill_date', 'attachment']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bill_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'expected_installments']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'expected_installments': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['item_type', 'inventory_item', 'description', 'quantity', 'unit_price']
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-control'}),
            'inventory_item': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class CombinedSaleItemForm(forms.Form):
    """Non-model form used on Create Sale page to capture the first line item.
    Supports two item types:
      - inventory: choose inventory_item; unit_price auto from inventory
      - machine: provide machine_name, description, quantity, unit_price
    """
    ITEM_TYPE_CHOICES = [
        ("inventory", "Inventory Item"),
        ("machine", "Machine"),
    ]

    item_type = forms.ChoiceField(choices=ITEM_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    machine_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))
    unit_price = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))

    def clean(self):
        cleaned = super().clean()
        item_type = cleaned.get('item_type')
        inv = cleaned.get('inventory_item')
        machine_name = cleaned.get('machine_name')
        description = cleaned.get('description')
        if item_type == 'inventory':
            if not inv:
                self.add_error('inventory_item', 'Select an inventory item')
            # Price will be forced in view from inventory
        elif item_type == 'machine':
            if not machine_name:
                self.add_error('machine_name', 'Machine name is required')
            if not description:
                self.add_error('description', 'Description is required')
        return cleaned