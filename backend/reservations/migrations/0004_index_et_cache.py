from django.core.management import call_command
from django.db import migrations

# Index sur les colonnes de recherche, créés seulement s'ils n'existent pas déjà
# (MySQL : base historique ; PostgreSQL : base neuve).
INDEX = [
    ('reservations', 'idx_reservations_salle_date',
     'id_salle, date_reservation, heure_debut'),
    ('rappels', 'idx_rappels_statut_date', 'statut, date_heure_prevue'),
    ('notifications', 'idx_notifications_reservation', 'id_reservation'),
]


def _index_existe(cursor, table, nom):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s",
        [table, nom],
    )
    return cursor.fetchone()[0] > 0


def _colonne_indexee(cursor, table, colonne):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = %s "
        "AND column_name = %s AND seq_in_index = 1",
        [table, colonne],
    )
    return cursor.fetchone()[0] > 0


def creer_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            for table, nom, colonnes in INDEX:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {nom} ON {table} ({colonnes})")
        return
    if schema_editor.connection.vendor != 'mysql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table, nom, colonnes in INDEX:
            premiere = colonnes.split(',')[0].strip()
            # Une clé étrangère MySQL est déjà indexée : on évite un doublon.
            if _index_existe(cursor, table, nom) or (
                ',' not in colonnes and _colonne_indexee(cursor, table, premiere)
            ):
                continue
            cursor.execute(f"CREATE INDEX {nom} ON {table} ({colonnes})")


def supprimer_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            for _, nom, _ in INDEX:
                cursor.execute(f"DROP INDEX IF EXISTS {nom}")
        return
    if schema_editor.connection.vendor != 'mysql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table, nom, _ in INDEX:
            if _index_existe(cursor, table, nom):
                cursor.execute(f"DROP INDEX {nom} ON {table}")


def creer_table_cache(apps, schema_editor):
    call_command('createcachetable', verbosity=0)


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0003_jeton_appareil'),
    ]

    operations = [
        migrations.RunPython(creer_index, supprimer_index),
        migrations.RunPython(creer_table_cache, migrations.RunPython.noop),
    ]
