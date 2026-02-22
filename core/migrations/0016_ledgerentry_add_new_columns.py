from django.db import migrations


def add_columns(apps, schema_editor):
    connection = schema_editor.connection

    if connection.vendor == 'postgresql':
        statements = [
            "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP;",
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
            "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'other';",
            "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS reference VARCHAR(100);",
            "ALTER TABLE core_ledgerentry ADD COLUMN IF NOT EXISTS description TEXT;",
        ]
        with connection.cursor() as cursor:
            for sql in statements:
                cursor.execute(sql)
    else:
        # SQLite path — check existing columns first
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(core_ledgerentry);")
            existing = {row[1] for row in cursor.fetchall()}

            columns_to_add = [
                ("timestamp", "TIMESTAMP"),
                ("source", "VARCHAR(20) DEFAULT 'other'"),
                ("reference", "VARCHAR(100)"),
                ("description", "TEXT"),
            ]
            for col_name, col_type in columns_to_add:
                if col_name not in existing:
                    cursor.execute(
                        f"ALTER TABLE core_ledgerentry ADD COLUMN {col_name} {col_type};"
                    )

            # Backfill timestamp from created_at if it exists
            if 'created_at' in existing:
                cursor.execute(
                    "UPDATE core_ledgerentry SET timestamp = created_at WHERE timestamp IS NULL;"
                )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_alter_ledgerentry_options_alter_ledgerentry_amount"),
    ]

    operations = [
        migrations.RunPython(add_columns, migrations.RunPython.noop),
    ]
