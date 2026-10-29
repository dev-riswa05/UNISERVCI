from django.conf import settings
from django.db import migrations, models

NOM_INDEX = 'uniq_utilisateur_email_minuscule'


def creer_index_email_unique(apps, schema_editor):
    """Un email ne peut appartenir qu'à un seul compte (sans tenir compte de la casse).

    L'email est l'identifiant de connexion : l'unicité est donc garantie par la
    base, pas seulement par les formulaires. MySQL ne gère pas cet index
    fonctionnel de la même façon : l'unicité y reste assurée par l'application.
    """
    if schema_editor.connection.vendor not in ('postgresql', 'sqlite'):
        return
    table = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {NOM_INDEX} "
            f"ON {table} (LOWER(email)) WHERE email <> ''"
        )


def supprimer_index_email_unique(apps, schema_editor):
    if schema_editor.connection.vendor not in ('postgresql', 'sqlite'):
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"DROP INDEX IF EXISTS {NOM_INDEX}")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservations', '0004_index_et_cache'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilrh',
            name='libelle',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.RunPython(creer_index_email_unique, supprimer_index_email_unique),
    ]
