from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Customer, InventoryItem, Sale, SaleItem, SalePayment


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SalesItemFilteringTotalsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(username='admin', password='pass123')
        self.client.login(username='admin', password='pass123')
        self.customer = Customer.objects.create(name='Acme Ltd', phone='123456')
        self.inv = InventoryItem.objects.create(
            part_name='Gear',
            part_code='G001',
            description='Steel gear',
            category='mechanical',
            quantity=50,
            unit='pcs',
            unit_price=100,
            location='A1',
            minimum_stock=5,
        )

    def test_sales_list_totals_filtered_by_machine(self):
        sale = Sale.objects.create(
            customer=self.customer,
            created_by=self.user,
            status='finalized',
        )
        SaleItem.objects.create(
            sale=sale,
            item_type='inventory',
            inventory_item=self.inv,
            quantity=5,
            unit_price=100,
        )
        SaleItem.objects.create(
            sale=sale,
            item_type='non_inventory',
            description='Machine X',
            quantity=1,
            unit_price=1000,
        )
        sale.recalc_total(save=True)
        SalePayment.objects.create(
            sale=sale,
            payment_date='2024-01-01',
            amount=800,
        )

        response = self.client.get(reverse('sale_list'), {'item_type': 'machine'}, follow=True)
        self.assertEqual(response.status_code, 200)

        total_sales = response.context['total_sales_amount']
        total_paid = response.context['total_paid_amount']
        total_due = response.context['total_due_amount']

        expected_sales = Decimal('1000')
        expected_paid = (Decimal('1000') / Decimal('1500')) * Decimal('800')
        expected_due = expected_sales - expected_paid

        self.assertEqual(total_sales, expected_sales)
        self.assertAlmostEqual(float(total_paid), float(expected_paid), places=2)
        self.assertAlmostEqual(float(total_due), float(expected_due), places=2)
