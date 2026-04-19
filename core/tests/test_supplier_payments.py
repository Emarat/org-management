from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import LedgerEntry, Supplier, SupplierPurchase, SupplierPurchasePayment


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    SECURE_SSL_REDIRECT=False,
)
class SupplierPaymentFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(username='admin_supplier', password='pass123')
        self.client.login(username='admin_supplier', password='pass123')

        self.supplier = Supplier.objects.create(name='ABC Supplier', phone='01700000000')
        self.purchase = SupplierPurchase.objects.create(
            supplier=self.supplier,
            product_name='Thread Roll',
            price=Decimal('1000.00'),
            paid_amount=Decimal('0.00'),
        )

    def test_partial_payments_update_purchase_balance(self):
        add_url = reverse('supplier_add_payment', args=[self.supplier.pk, self.purchase.pk])

        resp_first = self.client.post(add_url, {
            'amount': '500.00',
            'payment_date': '2026-04-19',
            'method': 'cash',
            'reference_number': '',
            'notes': 'First installment',
        })
        self.assertEqual(resp_first.status_code, 302)

        self.purchase.refresh_from_db()
        self.assertEqual(self.purchase.paid_amount, Decimal('500.00'))
        self.assertEqual(self.purchase.due, Decimal('500.00'))

        resp_second = self.client.post(add_url, {
            'amount': '500.00',
            'payment_date': '2026-04-20',
            'method': 'bank',
            'reference_number': 'BNK-7788',
            'notes': 'Final installment',
        })
        self.assertEqual(resp_second.status_code, 302)

        self.purchase.refresh_from_db()
        self.assertEqual(self.purchase.paid_amount, Decimal('1000.00'))
        self.assertEqual(self.purchase.due, Decimal('0.00'))
        self.assertEqual(self.purchase.payments.count(), 2)

    def test_reference_required_for_bank_payment(self):
        add_url = reverse('supplier_add_payment', args=[self.supplier.pk, self.purchase.pk])
        response = self.client.post(add_url, {
            'amount': '300.00',
            'payment_date': '2026-04-19',
            'method': 'bank',
            'reference_number': '',
            'notes': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reference number is required')
        self.assertEqual(SupplierPurchasePayment.objects.count(), 0)

    def test_overpayment_is_blocked(self):
        add_url = reverse('supplier_add_payment', args=[self.supplier.pk, self.purchase.pk])
        response = self.client.post(add_url, {
            'amount': '1200.00',
            'payment_date': '2026-04-19',
            'method': 'cash',
            'reference_number': '',
            'notes': 'Overpay attempt',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Payment exceeds remaining due amount')
        self.assertEqual(SupplierPurchasePayment.objects.count(), 0)

    def test_supplier_payment_creates_ledger_debit(self):
        add_url = reverse('supplier_add_payment', args=[self.supplier.pk, self.purchase.pk])
        self.client.post(add_url, {
            'amount': '400.00',
            'payment_date': '2026-04-19',
            'method': 'cash',
            'reference_number': '',
            'notes': 'Ledger test',
        })

        payment = SupplierPurchasePayment.objects.get()
        entry = LedgerEntry.objects.get(source='supplier_payment', reference=payment.receipt_number)
        self.assertEqual(entry.entry_type, 'debit')
        self.assertEqual(entry.amount, Decimal('400.00'))
