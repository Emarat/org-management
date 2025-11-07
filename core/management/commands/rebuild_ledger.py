from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Expense, SalePayment, Payment, LedgerEntry


class Command(BaseCommand):
    help = "Backfill the ledger from existing Expenses, SalePayments, and completed Payments. Skips existing entries by reference."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only report actions without writing.')

    def handle(self, *args, **options):
        dry = options.get('dry_run', False)
        created_count = 0

        def ensure_entry(entry_type, source, reference, description, amount):
            nonlocal created_count
            if not LedgerEntry.objects.filter(source=source, reference=reference).exists():
                if dry:
                    self.stdout.write(f"DRY-RUN: Would create {entry_type} {amount} from {source} ref={reference}")
                else:
                    LedgerEntry.objects.create(
                        entry_type=entry_type,
                        source=source,
                        reference=reference,
                        description=description[:255] if description else '',
                        amount=amount,
                    )
                created_count += 1

        with transaction.atomic():
            # Expenses -> debit
            for exp in Expense.objects.all().iterator():
                ref = f"EXP-{exp.id}"
                desc = f"{exp.get_category_display()} - {exp.description}" if exp.description else exp.get_category_display()
                ensure_entry('debit', 'expense', ref, desc, exp.amount)

            # SalePayments -> credit
            for sp in SalePayment.objects.select_related('sale').all().iterator():
                ref = sp.receipt_number
                desc = f"Payment for {sp.sale.sale_number}"
                ensure_entry('credit', 'sale_payment', ref, desc, sp.amount)

            # Standalone Payments (completed) -> credit as 'other'
            for p in Payment.objects.select_related('customer').filter(status='completed').iterator():
                ref = p.invoice_number
                amount = p.paid_amount or p.total_amount
                desc = f"Payment - {p.customer.name}"
                ensure_entry('credit', 'other', ref, desc, amount)

        self.stdout.write(self.style.SUCCESS(f"Rebuild complete. Entries created: {created_count}"))
