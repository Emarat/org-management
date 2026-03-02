from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from datetime import timedelta

from core.models import Customer, InventoryItem, Sale, SaleItem, SalePayment


class SalesFeatureTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # Superuser has all permissions
        self.user = User.objects.create_superuser(username='admin', password='pass123')
        self.client.login(username='admin', password='pass123')
        # Common inventory item
        self.inv = InventoryItem.objects.create(
            part_name='Gear', part_code='G001', description='Steel gear', category='mechanical',
            quantity=50, unit='pcs', unit_price=75, location='A1', minimum_stock=5
        )
        self.customer = Customer.objects.create(name='Acme Ltd', phone='123456')

    def test_sale_form_no_expected_installments_field(self):
        url = reverse('sale_create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn('expected_installments', html, 'expected_installments field still rendered')

    def test_create_inventory_item_sale_with_custom_price(self):
        """Inventory sale should respect a positive custom unit_price override."""
        url = reverse('sale_create')
        data = {
            'customer': str(self.customer.pk),
            'item_type': 'inventory',
            'inventory_item': str(self.inv.pk),
            'machine_name': '',
            'description': '',  # ignored for inventory
            'quantity': '3',
            'unit_price': '65',  # custom price lower than inventory price (75)
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        sale = Sale.objects.latest('id')
        item = sale.items.first()
        self.assertEqual(item.inventory_item, self.inv)
        self.assertEqual(item.unit_price, 65)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(sale.total_amount, item.unit_price * item.quantity)

    def test_create_machine_item_sale(self):
        url = reverse('sale_create')
        data = {
            'customer': str(self.customer.pk),
            'item_type': 'machine',
            'inventory_item': '',
            'machine_name': 'Lathe',
            'description': 'Precision lathe',
            'quantity': '2',
            'unit_price': '1500',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        sale = Sale.objects.latest('id')
        item = sale.items.first()
        self.assertEqual(item.item_type, 'non_inventory')
        self.assertIn('Lathe', item.description)
        self.assertIn('Precision lathe', item.description)
        self.assertEqual(item.unit_price, 1500)
        self.assertEqual(item.quantity, 2)

    def test_sale_list_item_type_filter(self):
        # Create inventory sale
        resp_inv_create = self.client.post(reverse('sale_create'), {
            'customer': str(self.customer.pk),
            'item_type': 'inventory',
            'inventory_item': str(self.inv.pk),
            'machine_name': '',
            'description': '',
            'quantity': '1',
            'unit_price': '0',
        })
        self.assertEqual(resp_inv_create.status_code, 302)
        inv_sale = Sale.objects.latest('id')
        inv_sale_number = inv_sale.sale_number
        # Create machine sale
        resp_machine_create = self.client.post(reverse('sale_create'), {
            'customer': str(self.customer.pk),
            'item_type': 'machine',
            'inventory_item': '',
            'machine_name': 'Lathe',
            'description': 'Precision',
            'quantity': '1',
            'unit_price': '2000',
        })
        self.assertEqual(resp_machine_create.status_code, 302)
        machine_sale = Sale.objects.latest('id')
        machine_sale_number = machine_sale.sale_number
        list_url = reverse('sale_list')
        # Inventory filter should include inventory sale number and exclude machine sale number
        resp_inv = self.client.get(list_url + '?item_type=inventory')
        self.assertEqual(resp_inv.status_code, 200)
        html_inv = resp_inv.content.decode()
        self.assertIn(inv_sale_number, html_inv)
        self.assertNotIn(machine_sale_number, html_inv)
        # Machine filter should include machine sale number and exclude inventory sale number
        resp_machine = self.client.get(list_url + '?item_type=machine')
        self.assertEqual(resp_machine.status_code, 200)
        html_machine = resp_machine.content.decode()
        self.assertIn(machine_sale_number, html_machine)
        self.assertNotIn(inv_sale_number, html_machine)
        # Inventory item description includes part name
        # Machine description includes machine label

    def test_customer_quick_add_ajax(self):
        url = reverse('customer_quick_add')
        payload = {
            'name': 'Rapid Co',
            'phone': '999',
            'company': 'Rapid',
            'email': 'rapid@example.com',
            'address': '123 Street',
            'city': 'Dhaka',
            'status': 'active',
            'notes': 'Test quick add'
        }
        resp = self.client.post(url, payload, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('id', data)
        self.assertIn('display', data)
        self.assertTrue(Customer.objects.filter(name='Rapid Co').exists())

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_sale_list_scopes_to_current_non_admin_user(self):
        User = get_user_model()
        sales_user = User.objects.create_user(username='sales1', password='pass123')
        other_user = User.objects.create_user(username='sales2', password='pass123')
        sales_user.user_permissions.add(Permission.objects.get(codename='view_sale'))

        own_sale = Sale.objects.create(
            customer=self.customer,
            created_by=sales_user,
            status='finalized',
            total_amount=1000,
        )
        SalePayment.objects.create(sale=own_sale, amount=300, method='cash')

        other_sale = Sale.objects.create(
            customer=self.customer,
            created_by=other_user,
            status='finalized',
            total_amount=2000,
        )
        SalePayment.objects.create(sale=other_sale, amount=700, method='cash')

        self.client.logout()
        self.client.login(username='sales1', password='pass123')
        resp = self.client.get(reverse('sale_list'), follow=True)

        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn(own_sale.sale_number, html)
        self.assertNotIn(other_sale.sale_number, html)
        self.assertEqual(resp.context['total_sales_amount'], 1000)
        self.assertEqual(resp.context['total_paid_amount'], 300)
        self.assertEqual(resp.context['total_due_amount'], 700)

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_sale_list_date_range_filter(self):
        User = get_user_model()
        sales_user = User.objects.create_user(username='sales_date', password='pass123')
        sales_user.user_permissions.add(Permission.objects.get(codename='view_sale'))

        old_sale = Sale.objects.create(
            customer=self.customer,
            created_by=sales_user,
            status='finalized',
            total_amount=500,
        )
        recent_sale = Sale.objects.create(
            customer=self.customer,
            created_by=sales_user,
            status='finalized',
            total_amount=900,
        )

        old_dt = timezone.now() - timedelta(days=10)
        Sale.objects.filter(pk=old_sale.pk).update(created_at=old_dt)

        self.client.logout()
        self.client.login(username='sales_date', password='pass123')

        start_date = (timezone.localdate() - timedelta(days=3)).isoformat()
        resp = self.client.get(reverse('sale_list'), {'start_date': start_date}, follow=True)
        self.assertEqual(resp.status_code, 200)

        html = resp.content.decode()
        self.assertIn(recent_sale.sale_number, html)
        self.assertNotIn(old_sale.sale_number, html)
