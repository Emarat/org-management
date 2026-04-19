from decimal import Decimal
import uuid

from django.db import migrations
from django.utils import timezone


def backfill_supplier_purchase_payments(apps, schema_editor):
    SupplierPurchase = apps.get_model('core', 'SupplierPurchase')
    SupplierPurchasePayment = apps.get_model('core', 'SupplierPurchasePayment')

    purchases = SupplierPurchase.objects.filter(paid_amount__gt=Decimal('0'))
    for purchase in purchases.iterator():
        if SupplierPurchasePayment.objects.filter(purchase_id=purchase.id).exists():
            continue

        now = timezone.now()
        SupplierPurchasePayment.objects.create(
            purchase_id=purchase.id,
            receipt_number=f"SPAYMIG-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
            amount=purchase.paid_amount,
            payment_date=purchase.purchase_date,
            method='cash',
            reference_number='',
            notes='Legacy migrated amount from SupplierPurchase.paid_amount',
        )


def noop_reverse(apps, schema_editor):
    # Keep migrated payment rows during reverse to avoid accidental data loss.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_alter_ledgerentry_source_supplierpurchasepayment'),
    ]

    operations = [
        migrations.RunPython(backfill_supplier_purchase_payments, reverse_code=noop_reverse),
    ]
