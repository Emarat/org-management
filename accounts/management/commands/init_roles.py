from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.conf import settings

ROLE_OWNER = 'Owner'
ROLE_MANAGER = 'Manager'
ROLE_FINANCE = 'Finance'
ROLE_EMPLOYEE = 'Employee'

ROLE_LIST = [ROLE_OWNER, ROLE_MANAGER, ROLE_FINANCE, ROLE_EMPLOYEE]

class Command(BaseCommand):
    help = 'Initialize default user role groups (Owner, Manager, Finance, Employee)'

    def handle(self, *args, **options):
        created = []
        for role in ROLE_LIST:
            group, was_created = Group.objects.get_or_create(name=role)
            if was_created:
                created.append(role)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created groups: {', '.join(created)}"))
        else:
            self.stdout.write("Role groups already exist. No changes.")
