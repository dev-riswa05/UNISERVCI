from django.core.management.base import BaseCommand
from django.utils import timezone

from reservations.models import Rappels, Participants
from reservations.emails import envoyer_rappel_reservation


class Command(BaseCommand):

    help = "Envoie les rappels de réservation arrivés à échéance."

    def handle(self, *args, **options):

        maintenant = timezone.now()

        rappels = Rappels.objects.filter(
            statut='EN_ATTENTE',
            date_heure_prevue__lte=maintenant
        )

        if not rappels.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Aucun rappel à envoyer."
                )
            )
            return

        for rappel in rappels:

            reservation = rappel.id_reservation

            # Ne pas envoyer si la réservation est annulée
            if reservation.statut == 'ANNULEE':

                rappel.statut = 'ANNULE'
                rappel.save(update_fields=['statut'])

                self.stdout.write(
                    self.style.WARNING(
                        f"Réservation {reservation.id_reservation} annulée."
                    )
                )
                continue

            participants = Participants.objects.filter(
                id_reservation=reservation
            )

            try:

                envoyer_rappel_reservation(
                    reservation,
                    participants
                )

                rappel.statut = 'ENVOYE'
                rappel.date_heure_envoi = timezone.now()

                rappel.save(
                    update_fields=[
                        'statut',
                        'date_heure_envoi'
                    ]
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Rappel envoyé pour la réservation "
                        f"{reservation.id_reservation}."
                    )
                )

            except Exception as erreur:

                self.stdout.write(
                    self.style.ERROR(
                        f"Erreur réservation "
                        f"{reservation.id_reservation} : {erreur}"
                    )
                )