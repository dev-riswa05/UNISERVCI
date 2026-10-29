from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
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

            # Réserve le rappel de façon atomique : deux exécutions
            # simultanées du planificateur ne l'envoient pas deux fois.
            with transaction.atomic():
                verrouille = Rappels.objects.select_for_update().get(pk=rappel.pk)
                if verrouille.statut != 'EN_ATTENTE':
                    continue
                verrouille.statut = 'EN_COURS'
                verrouille.save(update_fields=['statut'])
            rappel = verrouille

            reservation = rappel.id_reservation

            # Inutile de rappeler une réunion déjà terminée.
            fin_reunion = timezone.make_aware(
                datetime.combine(reservation.date_reservation, reservation.heure_fin)
            )
            if fin_reunion < maintenant:
                rappel.statut = 'ANNULE'
                rappel.save(update_fields=['statut'])
                continue

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

                # Remis en attente : sera retenté tant que la réunion n'est pas finie.
                rappel.statut = 'EN_ATTENTE'
                rappel.save(update_fields=['statut'])
                self.stdout.write(
                    self.style.ERROR(
                        f"Erreur réservation "
                        f"{reservation.id_reservation} : {erreur}"
                    )
                )