from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Grant baseline core RBAC permissions to role groups.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=str,
            default='Manager',
            help='Group name to grant core permissions to (default: Manager).',
        )

    def handle(self, *args, **options):
        group_name = options['group']
        group, _ = Group.objects.get_or_create(name=group_name)

        model_permission_map = {
            'customer': ['view_customer', 'add_customer', 'change_customer', 'delete_customer'],
            'inventoryitem': ['view_inventoryitem', 'add_inventoryitem', 'change_inventoryitem', 'delete_inventoryitem'],
            'expense': ['view_expense', 'add_expense', 'change_expense', 'delete_expense'],
        }

        expected_codenames = []
        permissions = []

        for model_name, codenames in model_permission_map.items():
            ct = ContentType.objects.get(app_label='core', model=model_name)
            expected_codenames.extend(codenames)
            permissions.extend(
                Permission.objects.filter(content_type=ct, codename__in=codenames)
            )

        access_control_ct, _ = ContentType.objects.get_or_create(app_label='core', model='accesscontrol')
        custom_codenames = [
            'view_customers_menu',
            'view_inventory_menu',
            'view_expenses_menu',
            'view_reports_menu',
            'submit_bill',
            'view_my_bills',
            'review_bills',
        ]
        expected_codenames.extend(custom_codenames)
        permissions.extend(
            Permission.objects.filter(content_type=access_control_ct, codename__in=custom_codenames)
        )

        found_codenames = {perm.codename for perm in permissions}
        missing = sorted(set(expected_codenames) - found_codenames)
        if missing:
            raise CommandError(
                'Missing permissions. Run migrations first. Missing: ' + ', '.join(missing)
            )

        group.permissions.add(*permissions)
        self.stdout.write(
            self.style.SUCCESS(
                f"Granted {len(found_codenames)} core permissions to group '{group_name}'."
            )
        )
