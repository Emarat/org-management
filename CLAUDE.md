# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 4.2 business management app for "Fashion Express" (customers, inventory, sales/quotations, payments, suppliers, expenses, bill claims, ledger/reports). Server-rendered Django templates + Bootstrap 5 from CDN. No frontend build step, no JS package manager.

## Commands

Requires **Python 3.8–3.12** (Django 4.2). See "Python version" below — 3.13+ runs the app but breaks the test suite.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Dev server — DJANGO_DEBUG must be a real shell env var, see "DEBUG gotcha" below
DJANGO_DEBUG=true python manage.py runserver

python manage.py makemigrations && python manage.py migrate
python manage.py createsuperuser

# Tests — modules MUST be named explicitly, see "Test discovery" below
python manage.py test core.tests.test_auth_rbac core.tests.test_inventory_list \
  core.tests.test_sale_create core.tests.test_sales_features \
  core.tests.test_sales_item_filtering core.tests.test_supplier_payments
python manage.py test core.tests.test_sale_create                      # one module
python manage.py test core.tests.test_sale_create.SaleCreateTests      # one class
python manage.py test core.tests.test_sale_create.SaleCreateTests.test_name  # one test

# RBAC / data bootstrap (run after migrate on a fresh DB)
python manage.py init_roles                      # creates Owner/Manager/Finance/Employee groups
python manage.py init_core_perms --group Manager # customer/inventory/expense + menu perms
python manage.py init_sales_perms --group Manager --user someone
python manage.py rebuild_ledger --dry-run        # backfill LedgerEntry from existing records

# Docker (Postgres + Gunicorn + WhiteNoise); entrypoint runs migrate + collectstatic
cp .env.example .env && docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

There is no linter/formatter configured for Python. Prettier is used only for non-template assets (`.prettierignore` excludes `templates/**/*.html` because it breaks Django template tags).

### Test discovery

`core/tests/` has **no `__init__.py`**, so plain `python manage.py test` discovers **0 tests** and silently reports success. Worse, discovery walks the repo root, imports the ad-hoc script `test_claims.py`, and executes its module-level code. Always name the test modules explicitly (see above), or add the missing `__init__.py`.

### Python version

Django 4.2 supports Python 3.8–3.12. On 3.13+ the app itself runs fine, but every test using the Django test client errors with `AttributeError: 'super' object has no attribute 'dicts'` (`django/template/context.py:__copy__`) — an upstream incompatibility, not a bug in this codebase. `psycopg2-binary==2.9.9` also has no wheel past 3.12 and fails to build, so a 3.13+ local env is SQLite-only. Use Python 3.12 or the Docker image (`python:3.11-slim`) when running tests or Postgres.

### DEBUG gotcha

`DJANGO_DEBUG` defaults to **false** (`org_management/settings.py:2`). With DEBUG off, settings enable `SECURE_SSL_REDIRECT`, HSTS, secure cookies, and WhiteNoise's `CompressedManifestStaticFilesStorage`. Running or testing without `DJANGO_DEBUG=true` therefore gives 301-to-https redirects and missing-manifest static errors. Existing tests work around this with a class decorator — copy it on any new view test:

```python
@override_settings(SECURE_SSL_REDIRECT=False,
                   STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
```

`DJANGO_DEBUG` **cannot be set via `.env`**: `DEBUG` is evaluated on line 2 of `settings.py`, before `load_dotenv()` runs further down the file. It must be exported in the shell. Every other env var (`SECRET_KEY`, `ALLOWED_HOSTS`, `POSTGRES_*`, `BRAND_*`) is read after the dotenv load and does work from `.env`.

Database is SQLite unless `POSTGRES_DB` is set, in which case Postgres is used — so do **not** `cp .env.example .env` for local SQLite development, as it sets `POSTGRES_*` (pointing at the Docker host `db`) and `DJANGO_DEBUG=False`. `.env.example` is meant for the Docker stack.

## Layout

- `org_management/` — settings, root URLconf. Everything env-driven via `.env` (loaded through `importlib` so linters don't need dotenv).
- `core/` — the entire business domain: `models.py` (~15 models), `views.py` (~3400 lines, all 66 views in one module), `forms.py`, `urls.py`, `admin.py`, `signals.py`, `middleware.py`, `permissions.py`.
- `accounts/` — `CustomUser` only (`AUTH_USER_MODEL = 'accounts.CustomUser'`). It absorbs the old Employee model: `position`, `department`, `salary`, `is_manager`, `status`, auto `employee_id`.
- `templates/` — project-level (not app-level); `base.html` holds the sidebar, all shared CSS, and the sidebar toggle JS.
- `api/index.py` — Vercel WSGI→ASGI shim (`vercel.json`); an alternative deploy target to Docker.
- `docs/` — feature notes; `docs/MULTI_SHOWROOM_PLAN.md` is the active plan for multi-showroom support (not yet implemented).

Root-level `check_data.py`, `fix_expense.py`, `list_users.py`, `set_manager.py`, `helper.py` are ad-hoc one-off scripts, not part of the app.

## Architecture

### Authorization — three overlapping mechanisms

1. **Django model permissions** — `@permission_required('core.add_sale', raise_exception=True)`, the dominant pattern in `views.py`.
2. **Synthetic "accesscontrol" permissions** — menu/action permissions with no backing model, created by *data migrations* (`core/migrations/0008_custom_permissions.py`, `0012_sales_permissions.py`) against a fake `ContentType(app_label='core', model='accesscontrol')`: `view_customers_menu`, `view_inventory_menu`, `view_expenses_menu`, `view_reports_menu`, `view_sales_menu`, `submit_bill`, `view_my_bills`, `review_bills`, `finalize_sale`. To add one, write a new data migration in the same style *and* add it to the relevant `init_*_perms` command. `templates/base.html` gates each sidebar entry on these.
3. **Manager/role checks** — `is_manager(user)` in `views.py` (superuser OR `user.is_manager` flag OR membership in group `Manager`) behind the `@manager_required` decorator, plus the group-based `role_required(...)` decorator in `core/permissions.py` and the `has_role` template filter in `core/templatetags/roles.py`.

Sale visibility is additionally scoped: `_visible_sales_queryset(user)` limits non-managers to sales they created; sale views must go through `_get_visible_sale_or_404`.

### Ledger

`LedgerEntry` is the single money-movement log, written **only by `post_save` signals** in `core/signals.py` (Expense→debit, SalePayment→credit, SupplierPurchasePayment→debit, completed Payment→credit). `_safe_create_ledger` dedupes on `(source, reference)`, so the ledger stays idempotent no matter which code path creates the record — never create `LedgerEntry` rows directly from views. `rebuild_ledger` backfills historical rows using the same reference conventions (`EXP-<id>`, receipt numbers, invoice numbers).

### Sale lifecycle

`quote` → `draft` → `finalized` (or `cancelled`). Stock is **not** touched until `Sale.finalize()`, which atomically validates and decrements both `quantity` and `box_count` on each linked `InventoryItem`, writes `StockHistory` rows (separate rows for boxes and loose units), and returns the items that dropped to low stock. Deleting a line item from an already-finalized sale restores inventory. `SaleItem.save()` recomputes `line_total` and calls `sale.recalc_total()`, so `Sale.total_amount` is a cache of the line items; `total_paid`/`balance_due` are computed from `SalePayment`.

Customer-level payments (`customer_add_payment`) create a `CustomerPaymentBatch`, allocate FIFO across that customer's outstanding sales under `select_for_update`, and materialize one `SalePayment` + `CustomerPaymentAllocation` per sale touched.

### Human-readable identifiers

Generated in `Model.save()` under `transaction.atomic()` + `select_for_update()` on singleton sequence rows: `Customer.customer_id` = `FE<DDMMYYYY>-NN` from `CustomerIdSequence` (pk=1), `Sale.sale_number` = `DD-MM-YYYY-FE-0001` from `SaleIdSequence` (pk=1, global never-reset counter despite the `date` column). Receipts use UUID suffixes (`RCPT-`, `SPAY-`, `CUSTPMT-`).

### Legacy

The standalone `Payment` model is deprecated in favour of `SalePayment` — its URLs are commented out in `core/urls.py` but the model, form, templates, and ledger signal remain. Don't build on it.

### Security middleware

`core/middleware.SecurityHeadersMiddleware` sets a CSP allowlisting `cdn.jsdelivr.net` / `cdnjs.cloudflare.com` (Bootstrap, Font Awesome). Adding any new external asset host requires editing that CSP. `script-src` includes `'unsafe-inline'` because page-specific JS is embedded in templates. `django-axes` locks accounts after 5 failures per username+IP.

`/admin/clean-all-data/` is a superuser-only destructive cleanup view (`core/admin.py`), double-gated on `DEBUG or ALLOW_DATA_CLEANUP=true` and on typing `CLEANUP_CONFIRMED`.
