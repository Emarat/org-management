from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Grant Sales baseline permissions to a group or user. Creates group if missing."

    def add_arguments(self, parser):
        parser.add_argument("--group", type=str, help="Group name to grant permissions to")
        parser.add_argument("--user", type=str, help="Username to grant permissions to")

    def handle(self, *args, **options):
        group_name = options.get("group")
        username = options.get("user")
        if not group_name and not username:
            raise CommandError("Provide --group or --user (or both)")

        # Custom permissions under synthetic accesscontrol type
        access_ct, _ = ContentType.objects.get_or_create(app_label="core", model="accesscontrol")
        custom_codenames = [
            "view_sales_menu",
            "finalize_sale",
        ]
        custom_perms = list(Permission.objects.filter(codename__in=custom_codenames, content_type=access_ct))

        # Model permissions
        sale_ct = ContentType.objects.get(app_label="core", model="sale")
        saleitem_ct = ContentType.objects.get(app_label="core", model="saleitem")
        model_codenames = [
            (sale_ct, ["view_sale", "add_sale", "change_sale"]),
            (saleitem_ct, ["add_saleitem", "change_saleitem"]),
        ]
        model_perms = []
        for ct, codes in model_codenames:
            model_perms.extend(list(Permission.objects.filter(content_type=ct, codename__in=codes)))

        all_perms = custom_perms + model_perms
        if not all_perms:
            raise CommandError("No permissions found. Did you run migrations?")

        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.add(*all_perms)
            self.stdout.write(self.style.SUCCESS(f"Granted {len(all_perms)} sales permissions to group '{group_name}'."))

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist")
            user.user_permissions.add(*all_perms)
            self.stdout.write(self.style.SUCCESS(f"Granted {len(all_perms)} sales permissions to user '{username}'."))
