from django.db import migrations


def add_columns(apps, schema_editor):
    """
    Add missing columns to core_ledgerentry for compatibility with the updated model:
    - timestamp (datetime)
    - source (varchar)
    - reference (varchar)
    - description (text)

    Populate timestamp from created_at when available.
    """
    # Raw SQL chosen to avoid issues with historical model state mismatches.
    statements = [
        # timestamp
        "ALTER TABLE core_ledgerentry ADD COLUMN timestamp datetime;",
        # backfill timestamp from created_at when present
        "UPDATE core_ledgerentry SET timestamp = created_at WHERE timestamp IS NULL;",
        # source with default 'other'
        "ALTER TABLE core_ledgerentry ADD COLUMN source varchar(20) DEFAULT 'other';",
        # reference and description optional
        "ALTER TABLE core_ledgerentry ADD COLUMN reference varchar(100);",
        "ALTER TABLE core_ledgerentry ADD COLUMN description text;",
    ]

    with schema_editor.connection.cursor() as cursor:
        for sql in statements:
            try:
                cursor.execute(sql)
            except Exception:
                # Column may already exist; ignore to keep migration idempotent in dev
                pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_alter_ledgerentry_options_alter_ledgerentry_amount"),
    ]

    operations = [
        migrations.RunPython(add_columns, migrations.RunPython.noop),
    ]
