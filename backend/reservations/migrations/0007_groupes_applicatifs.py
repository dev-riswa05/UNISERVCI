from django.db import migrations

GROUPES = ('SUPER_ADMIN', 'RH', 'MANAGER')


def creer_groupes(apps, schema_editor):
    """Crée les trois profils applicatifs sur toute base neuve.

    Ainsi un déploiement (ou une base de test) n'a pas besoin d'une commande
    manuelle : les profils existent dès `migrate`. Idempotent.
    """
    Group = apps.get_model('auth', 'Group')
    for nom in GROUPES:
        Group.objects.get_or_create(name=nom)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('reservations', '0006_salles_du_siege'),
    ]

    operations = [
        # Pas de suppression à l'annulation : des comptes peuvent en dépendre.
        migrations.RunPython(creer_groupes, migrations.RunPython.noop),
    ]
