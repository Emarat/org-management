from django.db import migrations


def create_custom_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Use a synthetic content type to host menu/action permissions
    content_type, _ = ContentType.objects.get_or_create(app_label='core', model='accesscontrol')

    permissions = [
        ('view_customers_menu', 'Can view Customers menu'),
        ('view_inventory_menu', 'Can view Inventory menu'),
        ('view_expenses_menu', 'Can view Expenses menu'),
        ('view_payments_menu', 'Can view Payments menu'),
        ('view_reports_menu', 'Can view Reports menu'),
        ('submit_bill', 'Can submit bill'),
        ('view_my_bills', 'Can view my bills'),
        ('review_bills', 'Can review bills'),
    ]

    for codename, name in permissions:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)


def drop_custom_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    try:
        content_type = ContentType.objects.get(app_label='core', model='accesscontrol')
    except ContentType.DoesNotExist:
        return
    Permission.objects.filter(
        content_type=content_type,
        codename__in=[
            'view_customers_menu',
            'view_inventory_menu',
            'view_expenses_menu',
            'view_payments_menu',
            'view_reports_menu',
            'submit_bill',
            'view_my_bills',
            'review_bills',
        ],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_squashed_migrations'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_custom_permissions, reverse_code=drop_custom_permissions),
    ]
