from django.db import migrations, models, transaction
import re
from django.utils import timezone

ID_PATTERN = re.compile(r'^FE(\d{8})-(\d+)$')

def backfill_customer_ids(apps, schema_editor):
    Customer = apps.get_model('core', 'Customer')
    Sequence = apps.get_model('core', 'CustomerIdSequence')

    with transaction.atomic():
        seq, _created = Sequence.objects.select_for_update().get_or_create(pk=1, defaults={'last_serial': 0})

        # If IDs already in new format, set sequence to max and exit.
        existing_new = Customer.objects.filter(customer_id__startswith='FE')
        if existing_new.exists():
            max_serial = seq.last_serial
            for cust in existing_new:  # derive max serial safely
                m = ID_PATTERN.match(cust.customer_id or '')
                if m:
                    serial = int(m.group(2))
                    if serial > max_serial:
                        max_serial = serial
            if max_serial != seq.last_serial:
                seq.last_serial = max_serial
                seq.save(update_fields=['last_serial'])
            return

        serial = seq.last_serial
        # Assign in chronological order for stability
        for cust in Customer.objects.all().order_by('created_at'):
            serial += 1
            date_part = (cust.created_at or timezone.now()).date().strftime('%d%m%Y')
            cust.customer_id = f"FE{date_part}-{serial:02d}"
            cust.save(update_fields=['customer_id'])
        seq.last_serial = serial
        seq.save(update_fields=['last_serial'])


def noop_reverse(apps, schema_editor):
    # Irreversible migration (old IDs discarded)
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerIdSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_serial', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Customer ID Sequence',
                'verbose_name_plural': 'Customer ID Sequences',
            },
        ),
        migrations.RunPython(backfill_customer_ids, noop_reverse),
    ]
