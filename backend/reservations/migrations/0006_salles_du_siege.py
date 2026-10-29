from django.db import migrations
from django.utils import timezone

ADRESSE = (
    "Siège UNISERV BTP Abidjan – Marcory Résidentiel, "
    "Avenue Ouezzin Coulibaly, Immeuble TIAMA"
)

# Salles du siège, créées sur toute base neuve (développement comme production).
# Chaque salle n'est créée que si son nom n'existe pas déjà : relancer la
# migration ne crée jamais de doublon et n'écrase aucune modification faite
# ensuite dans l'application (capacité, étage, activation...).
SALLES = [
    {'nom_salle': 'Salle de réunion 6e étage', 'etage': '6e étage'},
    {'nom_salle': 'Salle de réunion 4e étage', 'etage': '4e étage'},
    {'nom_salle': 'BUREAU DU DG', 'etage': '6e étage'},
]


def creer_salles(apps, schema_editor):
    Salles = apps.get_model('reservations', 'Salles')
    for salle in SALLES:
        Salles.objects.get_or_create(
            nom_salle=salle['nom_salle'],
            defaults={
                'localisation': ADRESSE,
                'etage': salle['etage'],
                'active': True,
                'date_creation': timezone.now(),
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0005_email_unique_et_libelle'),
    ]

    operations = [
        # Pas de suppression à l'annulation : des réservations peuvent exister.
        migrations.RunPython(creer_salles, migrations.RunPython.noop),
    ]
