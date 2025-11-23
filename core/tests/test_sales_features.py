from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Customer, InventoryItem, Sale, SaleItem


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

    def test_create_inventory_item_sale(self):
        url = reverse('sale_create')
        data = {
            'customer': str(self.customer.pk),
            'item_type': 'inventory',
            'inventory_item': str(self.inv.pk),
            'machine_name': '',
            'description': '',  # ignored for inventory
            'quantity': '3',
            'unit_price': '0',  # should be overridden by inventory unit_price
        }
        resp = self.client.post(url, data)
        # Redirect to sale_detail
        self.assertEqual(resp.status_code, 302)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.customer, self.customer)
        self.assertEqual(sale.items.count(), 1)
        item = sale.items.first()
        self.assertEqual(item.inventory_item, self.inv)
        self.assertEqual(item.unit_price, self.inv.unit_price)
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
