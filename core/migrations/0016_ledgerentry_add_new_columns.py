from django.db import migrations


def add_columns(apps, schema_editor):
    statements = [
    # timestamp
    "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP;",

    # backfill timestamp from created_at ONLY if that column exists
    """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'core_ledgerentry'
              AND column_name = 'created_at'
        ) THEN
            UPDATE core_ledgerentry
            SET timestamp = created_at
            WHERE timestamp IS NULL;
        END IF;
    END
    $$;
    """,

    # source with default
    "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'other';",

    # reference and description
    "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS reference VARCHAR(100);",
    "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS description TEXT;",
]


    with schema_editor.connection.cursor() as cursor:
        for sql in statements:
            cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_alter_ledgerentry_options_alter_ledgerentry_amount"),
    ]

    operations = [
        migrations.RunPython(add_columns, migrations.RunPython.noop),
    ]
