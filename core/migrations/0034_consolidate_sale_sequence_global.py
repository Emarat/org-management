from django.db import migrations
from django.utils import timezone


def consolidate_sale_sequence_global(apps, schema_editor):
    Sale = apps.get_model('core', 'Sale')
    SaleIdSequence = apps.get_model('core', 'SaleIdSequence')

    max_serial = 0
    for sale in Sale.objects.all().only('sale_number'):
        sale_number = sale.sale_number or ''
        if '-FE-' not in sale_number:
            continue
        try:
            serial = int(sale_number.rsplit('-FE-', 1)[1])
        except (TypeError, ValueError):
            continue
        if serial > max_serial:
            max_serial = serial

    today = timezone.now().date()
    base = SaleIdSequence.objects.filter(pk=1).first()
    if base is None:
        base = SaleIdSequence.objects.order_by('id').first()

    if base is None:
        SaleIdSequence.objects.create(pk=1, date=today, sequence_num=max_serial)
    else:
        if base.pk != 1:
            base.pk = 1
        base.date = base.date or today
        base.sequence_num = max(base.sequence_num or 0, max_serial)
        base.save()

    SaleIdSequence.objects.exclude(pk=1).delete()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_migrate_sale_numbers_to_new_format'),
    ]

    operations = [
        migrations.RunPython(consolidate_sale_sequence_global, reverse_noop),
    ]
