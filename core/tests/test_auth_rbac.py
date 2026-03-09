from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import Customer, Expense, InventoryItem


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
)
class RBACAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.employee = user_model.objects.create_user(username='emp1', password='pass123')
        self.manager = user_model.objects.create_user(
            username='mgr1',
            password='pass123',
            is_manager=True,
        )

        self.customer = Customer.objects.create(name='Client A', phone='0123456789')
        self.item = InventoryItem.objects.create(
            part_name='Part A',
            part_code='PART-A',
            quantity=10,
            unit='pcs',
            minimum_stock=1,
        )
        self.expense = Expense.objects.create(
            category='other',
            description='Test expense',
            amount=100,
        )

        # Grant manager a full baseline for customer/inventory/expense and bill submit routes.
        self._grant_permissions(
            self.manager,
            [
                'view_customer',
                'add_customer',
                'change_customer',
                'delete_customer',
                'view_inventoryitem',
                'add_inventoryitem',
                'change_inventoryitem',
                'delete_inventoryitem',
                'view_expense',
                'add_expense',
                'change_expense',
                'delete_expense',
                'submit_bill',
            ],
        )

    def _grant_permissions(self, user, codenames):
        perms = Permission.objects.filter(codename__in=codenames)
        user.user_permissions.add(*perms)

    def test_employee_forbidden_on_protected_core_routes(self):
        self.client.login(username='emp1', password='pass123')

        urls = [
            reverse('customer_list'),
            reverse('customer_detail', args=[self.customer.pk]),
            reverse('inventory_list'),
            reverse('inventory_stock_history', args=[self.item.pk]),
            reverse('expense_list'),
            reverse('expense_detail', args=[self.expense.pk]),
            reverse('submit_bill_claim'),
            reverse('reports'),
            reverse('export_excel'),
            reverse('customer_report_excel'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_manager_with_permissions_can_access_protected_routes(self):
        self.client.login(username='mgr1', password='pass123')

        urls = [
            reverse('customer_list'),
            reverse('customer_detail', args=[self.customer.pk]),
            reverse('inventory_list'),
            reverse('inventory_stock_history', args=[self.item.pk]),
            reverse('expense_list'),
            reverse('expense_detail', args=[self.expense.pk]),
            reverse('submit_bill_claim'),
            reverse('reports'),
            reverse('export_excel'),
            reverse('customer_report_excel'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_employee_forbidden_on_customer_crud_get_and_post(self):
        self.client.login(username='emp1', password='pass123')

        get_urls = [
            reverse('customer_add'),
            reverse('customer_edit', args=[self.customer.pk]),
            reverse('customer_delete', args=[self.customer.pk]),
            reverse('customer_quick_add'),
        ]
        for url in get_urls:
            with self.subTest(method='GET', url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

        post_cases = [
            (
                reverse('customer_add'),
                {'name': 'Denied Customer', 'phone': '01999999999'},
            ),
            (
                reverse('customer_edit', args=[self.customer.pk]),
                {'name': 'Blocked Edit', 'phone': '01888888888', 'status': 'active'},
            ),
            (reverse('customer_delete', args=[self.customer.pk]), {}),
            (
                reverse('customer_quick_add'),
                {'name': 'Denied Ajax', 'phone': '01777777777', 'status': 'active'},
            ),
        ]
        for url, payload in post_cases:
            with self.subTest(method='POST', url=url):
                response = self.client.post(url, payload)
                self.assertEqual(response.status_code, 403)

    def test_employee_forbidden_on_inventory_crud_get_and_post(self):
        self.client.login(username='emp1', password='pass123')

        get_urls = [
            reverse('inventory_add'),
            reverse('inventory_edit', args=[self.item.pk]),
            reverse('inventory_delete', args=[self.item.pk]),
        ]
        for url in get_urls:
            with self.subTest(method='GET', url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

        post_cases = [
            (
                reverse('inventory_add'),
                {
                    'part_name': 'Denied Item',
                    'part_code': 'DENIED-ITEM',
                    'quantity': '5',
                    'box_count': '0',
                    'unit': 'pcs',
                    'minimum_stock': '1',
                },
            ),
            (
                reverse('inventory_edit', args=[self.item.pk]),
                {
                    'part_name': 'Blocked Edit Item',
                    'part_code': self.item.part_code,
                    'quantity': '20',
                    'box_count': '0',
                    'unit': 'pcs',
                    'minimum_stock': '2',
                },
            ),
            (reverse('inventory_delete', args=[self.item.pk]), {}),
        ]
        for url, payload in post_cases:
            with self.subTest(method='POST', url=url):
                response = self.client.post(url, payload)
                self.assertEqual(response.status_code, 403)

    def test_employee_forbidden_on_expense_crud_get_and_post(self):
        self.client.login(username='emp1', password='pass123')

        get_urls = [
            reverse('expense_add'),
            reverse('expense_edit', args=[self.expense.pk]),
            reverse('expense_delete', args=[self.expense.pk]),
        ]
        for url in get_urls:
            with self.subTest(method='GET', url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

        post_cases = [
            (
                reverse('expense_add'),
                {
                    'date': timezone.localdate().isoformat(),
                    'category': 'other',
                    'description': 'Denied expense',
                    'amount': '321',
                },
            ),
            (
                reverse('expense_edit', args=[self.expense.pk]),
                {
                    'date': timezone.localdate().isoformat(),
                    'category': 'other',
                    'description': 'Blocked edit',
                    'amount': '999',
                },
            ),
            (reverse('expense_delete', args=[self.expense.pk]), {}),
        ]
        for url, payload in post_cases:
            with self.subTest(method='POST', url=url):
                response = self.client.post(url, payload)
                self.assertEqual(response.status_code, 403)

    def test_manager_can_perform_customer_crud(self):
        self.client.login(username='mgr1', password='pass123')

        create_response = self.client.post(
            reverse('customer_add'),
            {'name': 'New Customer', 'phone': '01666666666', 'status': 'active'},
        )
        self.assertEqual(create_response.status_code, 302)
        created = Customer.objects.get(name='New Customer')

        edit_response = self.client.post(
            reverse('customer_edit', args=[created.pk]),
            {'name': 'Updated Customer', 'phone': '01666666666', 'status': 'active'},
        )
        self.assertEqual(edit_response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.name, 'Updated Customer')

        delete_response = self.client.post(reverse('customer_delete', args=[created.pk]), {})
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=created.pk).exists())

    def test_manager_can_perform_inventory_and_expense_crud(self):
        self.client.login(username='mgr1', password='pass123')

        inventory_create = self.client.post(
            reverse('inventory_add'),
            {
                'part_name': 'Phase3 Item',
                'part_code': 'PHASE3-ITEM',
                'quantity': '7',
                'box_count': '0',
                'unit': 'pcs',
                'minimum_stock': '1',
            },
        )
        self.assertEqual(inventory_create.status_code, 302)
        new_item = InventoryItem.objects.get(part_code='PHASE3-ITEM')

        inventory_edit = self.client.post(
            reverse('inventory_edit', args=[new_item.pk]),
            {
                'part_name': 'Phase3 Item Updated',
                'part_code': 'PHASE3-ITEM',
                'quantity': '8',
                'box_count': '0',
                'unit': 'pcs',
                'minimum_stock': '2',
            },
        )
        self.assertEqual(inventory_edit.status_code, 302)
        new_item.refresh_from_db()
        self.assertEqual(str(new_item.quantity), '8.000')

        inventory_delete = self.client.post(reverse('inventory_delete', args=[new_item.pk]), {})
        self.assertEqual(inventory_delete.status_code, 302)
        self.assertFalse(InventoryItem.objects.filter(pk=new_item.pk).exists())

        expense_create = self.client.post(
            reverse('expense_add'),
            {
                'date': timezone.localdate().isoformat(),
                'category': 'other',
                'description': 'Phase3 expense',
                'amount': '150',
            },
        )
        form_errors = None
        if getattr(expense_create, 'context', None) and 'form' in expense_create.context:
            form_errors = expense_create.context['form'].errors
        self.assertEqual(expense_create.status_code, 302, form_errors)
        new_expense = Expense.objects.get(description='Phase3 expense')

        expense_edit = self.client.post(
            reverse('expense_edit', args=[new_expense.pk]),
            {
                'date': timezone.localdate().isoformat(),
                'category': 'other',
                'description': 'Phase3 expense edited',
                'amount': '175',
            },
        )
        self.assertEqual(expense_edit.status_code, 302)
        new_expense.refresh_from_db()
        self.assertEqual(new_expense.description, 'Phase3 expense edited')

        expense_delete = self.client.post(reverse('expense_delete', args=[new_expense.pk]), {})
        self.assertEqual(expense_delete.status_code, 302)
        self.assertFalse(Expense.objects.filter(pk=new_expense.pk).exists())
