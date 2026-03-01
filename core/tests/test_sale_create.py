from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Customer, InventoryItem, Sale, SalePayment


class SaleCreateViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass123', is_superuser=True)
        self.client.login(username='tester', password='pass123')
        self.customer = Customer.objects.create(name='Alpha Corp', phone='123', status='active')
        self.inv = InventoryItem.objects.create(
            part_name='Widget', part_code='W01', description='Test', category='general',
            quantity=100, unit='pcs', unit_price=50, location='A1', minimum_stock=5
        )

    def _formset_payload(self, total_forms=1):
        payload = {
            'items-TOTAL_FORMS': str(total_forms),
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
        }
        # Single inventory item row
        payload.update({
            'items-0-item_type': 'inventory',
            'items-0-inventory_item': str(self.inv.pk),
            'items-0-machine_name': '',
            'items-0-description': '',
            'items-0-quantity': '2',
            'items-0-unit_price': '0',  # will be overridden server-side
        })
        return payload

    def test_create_sale_with_initial_payment_and_single_item(self):
        url = reverse('sale_create')
        today = timezone.localdate()
        data = {
            'customer': str(self.customer.pk),
            'amount': '25',  # initial payment
            'payment_date': today.strftime('%Y-%m-%d'),
            'method': 'cash',
        }
        data.update(self._formset_payload())
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302, resp.context if hasattr(resp, 'context') else resp.status_code)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.customer, self.customer)
        # Items
        self.assertEqual(sale.items.count(), 1)
        item = sale.items.first()
        self.assertEqual(item.inventory_item, self.inv)
        self.assertEqual(item.unit_price, self.inv.unit_price)  # forced server-side
        self.assertEqual(item.quantity, 2)
        # Total
        self.assertEqual(float(sale.total_amount), float(self.inv.unit_price * 2))
        # Payment
        pay = SalePayment.objects.get(sale=sale)
        self.assertEqual(float(pay.amount), 25.0)
        self.assertEqual(pay.payment_date, today)

    def test_create_sale_after_removing_second_item(self):
        """Simulate user added a second row then removed it (so only index 0 submitted)."""
        url = reverse('sale_create')
        today = timezone.localdate()
        # After removal JS reindexes and TOTAL_FORMS becomes 1
        data = {
            'customer': str(self.customer.pk),
            'amount': '0',  # no initial payment
            'payment_date': today.strftime('%Y-%m-%d'),
            'method': '',
        }
        data.update(self._formset_payload())
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.items.count(), 1)
        self.assertEqual(float(sale.total_amount), float(self.inv.unit_price * 2))
        self.assertEqual(sale.payments.count(), 0)
