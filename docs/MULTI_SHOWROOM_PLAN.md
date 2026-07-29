# Multi-Showroom Adaptation Plan

**Project:** Fashion Express — org-management  
**Date:** 2026-07-29  
**Status:** Planning

---

## Background

The system currently operates as a single-location setup: one warehouse, one showroom. The business now requires support for **multiple showrooms** while keeping the warehouse central and shared.

All existing production data must be preserved. No breaking changes are permitted until a safe backfill has been confirmed.

---

## Guiding Principles

- **Warehouse is central.** `InventoryItem` and `StockHistory` do not change. All showrooms draw from the same stock pool.
- **Showrooms are sales points.** Only sales-side entities get showroom context.
- **Additive-first migrations.** All schema changes start nullable. Existing rows are backfilled before any constraint is tightened.
- **Permission model extends, not replaces.** The existing `is_manager` / superuser pattern is widened — not rewritten.

---

## What Changes vs. What Stays the Same

### Changes

| Entity | Change |
|--------|--------|
| `Sale` | Gets a `showroom` FK |
| `Expense` | Gets a `showroom` FK (`null` = central/warehouse expense) |
| `CustomUser` | Gets a `showroom` FK (primary assignment) |
| `CustomerPaymentBatch` | Gets a `showroom` FK |
| `SaleIdSequence` | Becomes per-showroom instead of global singleton |
| Sale number format | Gains showroom code: `{DD-MM-YYYY}-{CODE}-{serial:04d}` |
| Views / queries | Showroom-scoped filtering added |
| Forms | Showroom auto-assigned from logged-in user |
| Dashboard & Reports | Showroom filter added for admins |

### Stays the Same

| Entity | Reason |
|--------|--------|
| `InventoryItem` | Single warehouse — no location split |
| `StockHistory` | Already links to `InventoryItem`; sale number carries showroom info |
| `Customer` | Customers are global — they can visit any showroom |
| `Supplier` / `SupplierPurchase` / `SupplierPurchasePayment` | Warehouse-level procurement, unaffected |
| `BillClaim` | Already tied to `submitter`; user's showroom is sufficient context |
| `LedgerEntry` | Leave as-is; showroom context derivable from linked sale/expense if needed later |
| Auth / login / axes config | Untouched |

---

## New Model: `Showroom`

```python
class Showroom(models.Model):
    name       = models.CharField(max_length=200)
    code       = models.CharField(max_length=20, unique=True)  # e.g. "MAIN", "SHW2"
    address    = models.TextField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"
```

`code` is used in sale numbers and as a short human-readable identifier.

---

## Schema Changes (All Nullable — Phase 1)

Add the following FK fields. All are `null=True, blank=True` at this stage.

```python
# Sale
showroom = models.ForeignKey('Showroom', on_delete=models.PROTECT, null=True, blank=True, related_name='sales')

# Expense
showroom = models.ForeignKey('Showroom', on_delete=models.PROTECT, null=True, blank=True, related_name='expenses')
# null means "central / warehouse-level expense"

# CustomUser
showroom = models.ForeignKey('core.Showroom', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')

# CustomerPaymentBatch
showroom = models.ForeignKey('Showroom', on_delete=models.PROTECT, null=True, blank=True, related_name='payment_batches')
```

These are purely additive migrations — no existing column is altered.

---

## Sale Number Sequence: Per-Showroom

### Current

`SaleIdSequence` is a global singleton (`pk=1`). All sales share one counter.  
Format: `{DD-MM-YYYY}-FE-{serial:04d}`

### New

`SaleIdSequence` gets a `showroom` OneToOne FK. Each showroom has its own independent counter.  
Format: `{DD-MM-YYYY}-{showroom.code}-{serial:04d}`

```python
class SaleIdSequence(models.Model):
    showroom     = models.OneToOneField('Showroom', on_delete=models.CASCADE, related_name='sale_sequence')
    sequence_num = models.PositiveIntegerField(default=0)
```

**Existing sale numbers are unaffected** — they are stored as plain strings. The format change only applies to new sales created after the migration.

The existing singleton row (`pk=1`) is converted to a row linked to the `MAIN` showroom during the data migration.

---

## Data Migration (Phase 2)

A single Django data migration script performs the following steps **in order**:

1. Create `Showroom(name="Main Showroom", code="MAIN", is_active=True)`
2. `Sale.objects.update(showroom=main)`
3. `Expense.objects.update(showroom=main)`
4. `CustomerPaymentBatch.objects.update(showroom=main)`
5. `CustomUser.objects.update(showroom=main)`
6. Convert the existing `SaleIdSequence` singleton into a showroom-linked row for `MAIN`

This migration is safe to run on the live database. All FK columns are still nullable at this point, so there is no constraint risk.

---

## Permission Model

The current access pattern is extended — not replaced.

| Role | Access |
|------|--------|
| `is_superuser` | All showrooms, all data |
| `is_manager=True` + showroom assigned | All data within their showroom |
| Regular staff | Only their own records within their showroom |

### Current helper (views.py)

```python
def _visible_sales_queryset(user):
    qs = Sale.objects.select_related('customer').all()
    if _can_view_all_sales(user):
        return qs
    return qs.filter(created_by=user)
```

### Updated helper

```python
def _visible_sales_queryset(user):
    qs = Sale.objects.select_related('customer', 'showroom').all()
    if user.is_superuser:
        return qs                                       # all showrooms
    if getattr(user, 'is_manager', False):
        return qs.filter(showroom=user.showroom)        # their showroom only
    return qs.filter(created_by=user)                  # own sales only
```

The same pattern applies to `Expense`, `CustomerPaymentBatch`, and any other showroom-scoped querysets.

---

## UI & Form Changes

### Sale Create Form
- Showroom is **auto-assigned** from `request.user.showroom` for regular staff and showroom managers.
- Superusers get a dropdown to select any active showroom.
- No manual selection for staff — prevents assigning sales to the wrong location.

### Expense Form
- Showroom pre-filled from the logged-in user's showroom.
- Superusers/admins can set showroom to `null` ("Central") for warehouse or HQ-level expenses.

### Customer Payment Form
- Showroom inherited from the user recording the payment.

### Dashboard
- Staff and showroom managers see metrics for their showroom only.
- Superusers see a showroom selector or an aggregated "all showrooms" view.

### Reports & Exports
- Add a showroom filter dropdown on: Sales list, Expense list, Reports page, Ledger.
- Superusers can select "All Showrooms" to get a combined view.
- Excel/PDF exports include a showroom column.

---

## Deployment Order (Production-Safe)

Each step is independently deployable. Roll back any step without affecting the previous.

```
Step 1 — Deploy Showroom model migration
         Adds new table only. Zero risk. No existing table touched.

Step 2 — Deploy nullable FK migrations
         Adds showroom FK columns as NULL to Sale, Expense,
         CustomUser, CustomerPaymentBatch. Zero risk.

Step 3 — Run data migration
         Creates MAIN showroom, backfills all existing rows,
         converts SaleIdSequence to per-showroom.
         Safe: all FKs still nullable.

Step 4 — Deploy updated SaleIdSequence model
         Adds showroom OneToOne FK to sequence table.
         Existing MAIN sequence row already converted in Step 3.

Step 5 — Deploy updated views, forms, and templates
         Showroom-aware queries, auto-assign on forms,
         dashboard and report filters.

Step 6 — QA & verify
         Confirm all existing data has showroom assigned.
         Confirm new sales carry correct showroom.

Step 7 — (Optional, later) Make FKs non-nullable on Sale
         Only after Step 6 is confirmed clean.
         Expense showroom stays nullable (central expenses are valid).
```

---

## Risk Assessment

| Change | Risk Level | Notes |
|--------|------------|-------|
| Add `Showroom` model | None | New table, no existing schema touched |
| Add nullable FKs | None | Additive only |
| Data migration (backfill) | Very Low | Plain UPDATE statements, rollback by nulling FKs |
| Per-showroom `SaleIdSequence` | Low | Existing sale number strings are untouched |
| View / query changes | Low | Extends existing pattern, superuser path unchanged |
| Form auto-assign | None | Default value set from user context |
| Make FKs non-nullable (Step 7) | Low | Only after full backfill is verified |

---

## Open Questions (Decide Before Implementation)

1. **Customer ownership** — Should a customer record be loosely associated with the showroom where they first registered? (Recommended: no FK on Customer, but record the creating user's showroom at creation time if needed for reporting.)

2. **Inventory transfers** — Do showrooms ever hold physical stock separately (e.g., a display unit), or is all stock always counted centrally? If showrooms ever need local stock counts, a `ShowroomStock` model will be needed later.

3. **Expense split** — Is there a "head office" category of expense separate from both showrooms and warehouse? If so, `null` showroom on Expense covers this.

4. **Showroom manager role** — Should `is_manager=True` always mean showroom-scoped, or should there be a separate flag (e.g., `is_admin`) for system-wide managers? Currently `is_superuser` covers system-wide — `is_manager` can safely mean "showroom manager."

5. **Sale number reset** — Does each showroom's serial start from 0001, or continue from the current global counter? Recommended: start from 0001 per showroom for clarity.
