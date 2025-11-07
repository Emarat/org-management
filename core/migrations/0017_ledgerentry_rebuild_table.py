from django.db import migrations, connection


def rebuild_ledgerentry_table(apps, schema_editor):
    """For SQLite databases that still have legacy columns (e.g., NOT NULL note),
    rebuild the table to match the current model schema and drop obsolete columns.
    Safe to run multiple times; skips when schema already matches.
    """
    vendor = connection.vendor
    if vendor != 'sqlite':
        # No-op for non-SQLite backends; rely on standard migrations elsewhere
        return

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_ledgerentry)")
        cols = cursor.fetchall()
        col_names = {c[1] for c in cols}
        # If legacy 'note' column exists, rebuild
        if 'note' not in col_names:
            return

        cursor.execute("PRAGMA foreign_keys=off;")
        # Create new table per current model definition
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS core_ledgerentry__new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp datetime NOT NULL,
                entry_type varchar(10) NOT NULL,
                source varchar(20) NOT NULL DEFAULT 'other',
                reference varchar(100) NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                amount decimal NOT NULL
            );

            INSERT INTO core_ledgerentry__new (id, timestamp, entry_type, source, reference, description, amount)
            SELECT
                id,
                COALESCE(timestamp, created_at),
                entry_type,
                COALESCE(source, 'other'),
                COALESCE(reference, ''),
                COALESCE(description, note, ''),
                amount
            FROM core_ledgerentry;

            DROP TABLE core_ledgerentry;
            ALTER TABLE core_ledgerentry__new RENAME TO core_ledgerentry;
            """
        )
        cursor.execute("PRAGMA foreign_keys=on;")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_ledgerentry_add_new_columns'),
    ]

    operations = [
        migrations.RunPython(rebuild_ledgerentry_table, migrations.RunPython.noop),
    ]
