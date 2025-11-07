from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Expense, SalePayment, LedgerEntry, Payment


def _safe_create_ledger(entry_type: str, source: str, reference: str, description: str, amount):
    """Create a ledger entry if one with the same source+reference doesn't already exist.
    Keeps ledger idempotent across multiple creation paths (views, signals, imports).
    """
    try:
        exists = LedgerEntry.objects.filter(source=source, reference=reference).exists()
        if not exists:
            LedgerEntry.objects.create(
                entry_type=entry_type,
                source=source,
                reference=reference,
                description=description[:255] if description else '',
                amount=amount,
            )
    except Exception:
        # Never block the main flow on ledger issues
        pass


@receiver(post_save, sender=Expense)
def create_ledger_for_expense(sender, instance: Expense, created, **kwargs):
    """Ensure every Expense creates a matching debit ledger entry.
    Works for expenses created via forms or programmatically (e.g., bill claim approval).
    """
    try:
        # Reference format used elsewhere for consistency
        reference = f"EXP-{instance.id}"
        description = f"{instance.get_category_display()} - {instance.description}" if instance.description else instance.get_category_display()
        # Only create on first save; idempotency guard inside _safe_create_ledger
        if created:
            _safe_create_ledger(
                entry_type='debit',
                source='expense',
                reference=reference,
                description=description,
                amount=instance.amount,
            )
    except Exception:
        # Do not break Expense save
        pass


@receiver(post_save, sender=SalePayment)
def create_ledger_for_sale_payment(sender, instance: SalePayment, created, **kwargs):
    """Ensure every SalePayment creates a matching credit ledger entry.
    """
    try:
        reference = instance.receipt_number
        description = f"Payment for {instance.sale.sale_number}"
        if created:
            _safe_create_ledger(
                entry_type='credit',
                source='sale_payment',
                reference=reference,
                description=description,
                amount=instance.amount,
            )
    except Exception:
        pass


@receiver(post_save, sender=Payment)
def create_ledger_for_payment(sender, instance: Payment, created, **kwargs):
    """Optional: Mirror standalone Payments into the ledger as credits when completed.
    This covers the /payments/ flow which is distinct from SalePayment.
    Uses source='other' to avoid expanding choices/migrations.
    Idempotent by invoice_number reference.
    """
    try:
        if instance.status == 'completed':
            reference = instance.invoice_number
            # Prefer paid_amount if present; fallback to total_amount
            amount = instance.paid_amount or instance.total_amount
            desc = f"Payment - {instance.customer.name}"
            _safe_create_ledger(
                entry_type='credit',
                source='other',
                reference=reference,
                description=desc,
                amount=amount,
            )
    except Exception:
        pass
