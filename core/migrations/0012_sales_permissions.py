from django.db import migrations


def create_sales_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    content_type, _ = ContentType.objects.get_or_create(app_label='core', model='accesscontrol')

    permissions = [
        ('view_sales_menu', 'Can view Sales menu'),
        ('finalize_sale', 'Can finalize a sale'),
    ]

    for codename, name in permissions:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)


def drop_sales_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    try:
        content_type = ContentType.objects.get(app_label='core', model='accesscontrol')
    except ContentType.DoesNotExist:
        return
    Permission.objects.filter(
        content_type=content_type,
        codename__in=['view_sales_menu', 'finalize_sale'],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_sale_finalized_at_sale_finalized_by'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_sales_permissions, reverse_code=drop_sales_permissions),
    ]
