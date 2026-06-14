from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import InventoryItem


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
)
class InventoryListSummaryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.manager = user_model.objects.create_user(
            username='inv_mgr',
            password='pass123',
            is_manager=True,
        )
        permission = Permission.objects.get(codename='view_inventoryitem')
        self.manager.user_permissions.add(permission)

        InventoryItem.objects.create(
            part_name='Mango Alpha',
            part_code='MANGO-001',
            category='Fruit',
            quantity=Decimal('2'),
            box_count=1,
            unit='pcs',
            unit_price=Decimal('10.00'),
            minimum_stock=1,
        )
        InventoryItem.objects.create(
            part_name='Mango Beta',
            part_code='MANGO-002',
            category='Fruit',
            quantity=Decimal('3'),
            box_count=2,
            unit='pcs',
            unit_price=Decimal('15.00'),
            minimum_stock=1,
        )
        InventoryItem.objects.create(
            part_name='Mango Gamma',
            part_code='MANGO-003',
            category='Fruit',
            quantity=Decimal('1'),
            box_count=3,
            unit='pcs',
            unit_price=Decimal('5.00'),
            minimum_stock=1,
        )
        InventoryItem.objects.create(
            part_name='Apple',
            part_code='APPLE-001',
            category='Fruit',
            quantity=Decimal('7'),
            box_count=4,
            unit='pcs',
            unit_price=Decimal('20.00'),
            minimum_stock=1,
        )

    def test_inventory_search_shows_filtered_totals(self):
        self.client.login(username='inv_mgr', password='pass123')

        initial_response = self.client.get(reverse('inventory_list'))
        self.assertEqual(initial_response.status_code, 200)
        self.assertNotContains(initial_response, 'Matching Items')
        self.assertNotContains(initial_response, 'Total Stock Value')

        response = self.client.get(reverse('inventory_list'), {'q': 'mango'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['inventory_summary']['matching_items'], 3)
        self.assertEqual(response.context['inventory_summary']['total_quantity'], Decimal('6'))
        self.assertEqual(response.context['inventory_summary']['total_boxes'], 6)
        self.assertEqual(response.context['inventory_summary']['total_stock_value'], Decimal('70'))
        self.assertContains(response, 'Matching Items')
        self.assertContains(response, 'Total Quantity')
        self.assertContains(response, 'Total Boxes')
        self.assertContains(response, 'Total Stock Value')
        self.assertContains(response, '6.000')
        self.assertContains(response, '৳&nbsp;70.00')
        self.assertContains(response, 'MANGO-001')
        self.assertContains(response, 'MANGO-002')
        self.assertContains(response, 'MANGO-003')
        self.assertNotContains(response, 'APPLE-001')