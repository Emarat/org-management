from django.db import migrations


def create_dashboard_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Reuse the synthetic content type used for menu/action permissions
    content_type, _ = ContentType.objects.get_or_create(app_label='core', model='accesscontrol')

    permissions = [
        ('view_dashboard', 'Can view Dashboard page'),
        ('view_dashboard_menu', 'Can view Dashboard menu'),
    ]

    for codename, name in permissions:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)


def drop_dashboard_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    try:
        content_type = ContentType.objects.get(app_label='core', model='accesscontrol')
    except ContentType.DoesNotExist:
        return
    Permission.objects.filter(
        content_type=content_type,
        codename__in=[
            'view_dashboard',
            'view_dashboard_menu',
        ],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_custom_permissions'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_dashboard_permissions, reverse_code=drop_dashboard_permissions),
    ]
