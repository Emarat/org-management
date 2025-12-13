from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_alter_inventoryitem_unit_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saleitem",
            name="description",
            field=models.TextField(blank=True, help_text="Required for non-inventory items"),
        ),
    ]
