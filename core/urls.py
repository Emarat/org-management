from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customers/quick-add/', views.customer_quick_add, name='customer_quick_add'),
    
    # Inventory URLs
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_add, name='inventory_add'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),
    
    # Expense URLs
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    # Payment URLs - DEPRECATED: Legacy payment system, replaced by SalePayment
    # path('payments/', views.payment_list, name='payment_list'),
    # path('payments/add/', views.payment_add, name='payment_add'),
    # path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    # path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # Bill Claim URLs
    path('claims/', views.list_bill_claims, name='list_bill_claims'),
    path('claims/my/', views.my_bill_claims, name='my_bill_claims'),
    path('claims/submit/', views.submit_bill_claim, name='submit_bill_claim'),
    path('claims/<int:pk>/approve/', views.approve_bill_claim, name='approve_bill_claim'),
    path('claims/<int:pk>/reject/', views.reject_bill_claim, name='reject_bill_claim'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/ledger/', views.ledger, name='ledger'),
    path('reports/export-excel/', views.export_excel, name='export_excel'),

    # Sales URLs
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/new/', views.sale_create, name='sale_create'),
    path('sales/new/unified/', views.sale_create_unified, name='sale_create_unified'),
    path('sales/new/quote/', views.sale_quote_create, name='sale_quote_create'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/convert/', views.sale_convert_to_invoice, name='sale_convert_to_invoice'),
    path('sales/<int:pk>/invoice/', views.sale_invoice, name='sale_invoice'),
    path('sales/<int:pk>/add-item/', views.sale_add_item, name='sale_add_item'),
    path('sales/<int:pk>/items/<int:item_pk>/delete/', views.sale_delete_item, name='sale_delete_item'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),
    path('sales/<int:pk>/finalize/', views.sale_finalize, name='sale_finalize'),
    path('sales/<int:pk>/add-payment/', views.sale_add_payment, name='sale_add_payment'),
    path('sales/<int:pk>/payments/export.csv', views.sale_payments_export, name='sale_payments_export'),
    path('sales/<int:sale_pk>/payments/<int:payment_pk>/receipt/', views.sale_payment_receipt, name='sale_payment_receipt'),
]
