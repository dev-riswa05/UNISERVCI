"""Contrôles d'intégration non destructifs de la V1.

La commande exécute les principaux parcours API dans une transaction forcée
en rollback. Elle peut donc être lancée sur la base locale sans conserver la
réservation technique créée pendant les tests.
"""

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from reservations.emails import envoyer_confirmation_reservation
from reservations.models import (
    Participants,
    Rappels,
    Reservations,
    Salles,
    Utilisateurs,
    ProfilRH,
    SessionRH,
)
from reservations.permissions import DISPLAY_GROUP


class Command(BaseCommand):
    help = "Vérifie les parcours critiques de la V1 sans conserver de données."

    def handle(self, *args, **options):
        self.results = []

        with override_settings(ALLOWED_HOSTS=['testserver']):
            self._run_checks()

        for name, detail in self.results:
            suffix = f" — {detail}" if detail else ""
            self.stdout.write(self.style.SUCCESS(f"OK   {name}{suffix}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nRÉSUMÉ : {len(self.results)} contrôles réussis."
            )
        )
        self.stdout.write(
            "NETTOYAGE : transaction annulée, aucune donnée de test conservée."
        )

    def _check(self, name, condition, detail=''):
        if not condition:
            raise CommandError(f"ÉCHEC — {name}: {detail}")
        self.results.append((name, detail))

    def _run_checks(self):
        user_model = get_user_model()
        django_user = (
            user_model.objects.filter(username='rh_demo').first()
            or user_model.objects.first()
        )
        room = Salles.objects.filter(active=True).first()
        business_user = Utilisateurs.objects.filter(
            id_utilisateur=1,
            actif=True
        ).first()

        self._check('Compte Django disponible', django_user is not None)
        self._check('Salle active disponible', room is not None)
        self._check('Profil RH métier #1 disponible', business_user is not None)

        anonymous = APIClient()
        self._check(
            'Planning protégé sans token',
            anonymous.get('/api/planning/').status_code == 401
        )
        self._check(
            'Disponibilité protégée sans token',
            anonymous.get(
                '/api/salles/disponibles/?date=2099-12-31'
                '&heure_debut=08:00&heure_fin=09:00'
            ).status_code == 401
        )
        public_display = anonymous.get('/api/affichage/?date=2099-12-31')
        self._check(
            'Affichage salles protégé sans token',
            public_display.status_code == 401
        )

        # Les RH utilisent une session liée au profil humain sélectionné.
        # Un simple force_authenticate ne reproduirait plus la sécurité réelle.
        profile = ProfilRH.objects.filter(nom='WARIS', actif=True).first()
        self._check('Profil RH WARIS disponible', profile is not None)
        session = SessionRH.objects.create(utilisateur=django_user, profil=profile)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {session.key}')
        self._check(
            'Créneau avant 08h00 refusé',
            client.get(
                '/api/salles/disponibles/?date=2099-12-31'
                '&heure_debut=07:30&heure_fin=08:30'
            ).status_code == 400
        )
        self._check(
            'Créneau après 17h30 refusé',
            client.get(
                '/api/salles/disponibles/?date=2099-12-31'
                '&heure_debut=17:00&heure_fin=18:00'
            ).status_code == 400
        )

        # Une date très éloignée évite les collisions avec le planning réel.
        payload = {
            'id_salle': room.id_salle,
            'nom_demandeur': 'Test intégration Codex',
            'email_demandeur': 'integration.test@uniservci.net',
            'objet': 'Vérification V1 — donnée temporaire',
            'date_reservation': '2099-12-31',
            'heure_debut': '08:00:00',
            'heure_fin': '09:00:00',
            'nombre_participants': 2,
            'notes': 'Cette donnée sera annulée par transaction.',
            'participants': [
                {
                    'nom': 'Participant Un',
                    'email': 'participant1@example.test',
                },
                {
                    'nom': 'Participant Deux',
                    'email': 'participant2@example.test',
                },
            ],
        }

        # Le rollback placé dans finally garantit le nettoyage même si un
        # contrôle échoue au milieu du scénario.
        with transaction.atomic():
            try:
                self._check_reservation_flow(
                    client,
                    django_user,
                    business_user,
                    room,
                    payload,
                )
            finally:
                transaction.set_rollback(True)

    def _check_reservation_flow(
        self,
        client,
        django_user,
        business_user,
        room,
        payload,
    ):
        display_user = get_user_model().objects.filter(
            groups__name=DISPLAY_GROUP,
            is_active=True
        ).first()
        self._check(
            'Compte technique AFFICHAGE disponible',
            display_user is not None
        )
        display_client = APIClient()
        display_client.force_authenticate(user=display_user)

        display_response = display_client.get(
            '/api/affichage/?date=2099-12-31'
        )
        self._check(
            'Profil AFFICHAGE autorisé sur son endpoint',
            display_response.status_code == 200
        )
        self._check(
            'Affichage tablette sans données sensibles',
            set(display_response.data.keys()) == {
                'date', 'salles', 'reservations'
            }
        )
        self._check(
            'Profil AFFICHAGE refusé sur les salles RH',
            display_client.get('/api/salles/').status_code == 403
        )
        self._check(
            'Profil AFFICHAGE refusé sur le planning RH',
            display_client.get('/api/planning/').status_code == 403
        )
        self._check(
            'Profil AFFICHAGE refusé en création',
            display_client.post('/api/reservations/', {}, format='json').status_code == 403
        )

        role_response = display_client.get('/api/me/')
        self._check(
            'Session AFFICHAGE retourne le bon rôle',
            role_response.status_code == 200
            and role_response.data['role'] == DISPLAY_GROUP
        )

        created = client.post('/api/reservations/', payload, format='json')
        self._check('Création réservation', created.status_code == 201, created.data)

        reservation_id = created.data['id_reservation']
        reservation = Reservations.objects.get(id_reservation=reservation_id)
        self._check(
            'RH attribué côté serveur',
            reservation.id_utilisateur_id == business_user.id_utilisateur
        )
        self._check(
            'Statut confirmé côté serveur',
            reservation.statut == 'CONFIRMEE'
        )
        self._check(
            'Deux participants créés',
            Participants.objects.filter(id_reservation=reservation).count() == 2
        )

        reminder = Rappels.objects.get(id_reservation=reservation)
        self._check(
            'Rappel H-2 créé',
            reminder.date_heure_prevue.hour == 6,
            reminder.date_heure_prevue
        )

        detail = client.get(f'/api/reservations/{reservation_id}/')
        self._check(
            'Participants lisibles en détail',
            detail.status_code == 200 and len(detail.data['participants']) == 2
        )

        conflict = client.post('/api/reservations/', payload, format='json')
        self._check(
            'Conflit même salle refusé',
            conflict.status_code == 400,
            conflict.data
        )

        availability = client.get(
            '/api/salles/disponibles/?date=2099-12-31'
            '&heure_debut=08:00&heure_fin=09:00'
        )
        available_ids = [item['id_salle'] for item in availability.data]
        self._check(
            'Salle occupée retirée des disponibilités',
            availability.status_code == 200
            and room.id_salle not in available_ids
        )

        edit_availability = client.get(
            '/api/salles/disponibles/?date=2099-12-31'
            '&heure_debut=08:00&heure_fin=09:00'
            f'&exclure_reservation={reservation_id}'
        )
        edit_ids = [item['id_salle'] for item in edit_availability.data]
        self._check(
            'Réservation courante exclue du conflit',
            room.id_salle in edit_ids
        )

        modified = client.patch(
            f'/api/reservations/{reservation_id}/',
            {
                'heure_debut': '09:00:00',
                'heure_fin': '10:00:00',
                'participants': [{
                    'nom': 'Participant Modifié',
                    'email': 'modifie@example.test',
                }],
                'nombre_participants': 1,
            },
            format='json'
        )
        self._check(
            'Modification réservation',
            modified.status_code == 200,
            modified.data
        )

        reminder.refresh_from_db()
        self._check(
            'Participants remplacés',
            Participants.objects.filter(id_reservation=reservation).count() == 1
        )
        self._check(
            'Rappel recalculé après modification',
            reminder.date_heure_prevue.hour == 7,
            reminder.date_heure_prevue
        )

        planning = client.get('/api/planning/?date=2099-12-31')
        self._check(
            'Réservation visible au planning',
            planning.status_code == 200 and any(
                item['id_reservation'] == reservation_id
                for item in planning.data
            )
        )

        public_display = display_client.get(
            f'/api/affichage/?date=2099-12-31&id_salle={room.id_salle}'
        )
        public_meeting = next(
            item for item in public_display.data['reservations']
            if item['id_reservation'] == reservation_id
        )
        self._check(
            'Filtre salle de l’affichage tablette',
            public_display.status_code == 200
            and public_meeting['id_salle'] == room.id_salle
        )
        self._check(
            'Réservation tablette limitée aux champs autorisés',
            set(public_meeting.keys()) == {
                'id_reservation',
                'id_salle',
                'salle_nom',
                'objet',
                'date_reservation',
                'heure_debut',
                'heure_fin',
            }
        )

        # Locmem intercepte les messages : aucun e-mail ne quitte la machine.
        with override_settings(
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
        ):
            envoyer_confirmation_reservation(
                reservation,
                Participants.objects.filter(id_reservation=reservation)
            )
            self._check(
                'E-mails demandeur et participant générés',
                len(mail.outbox) == 2,
                f'{len(mail.outbox)} e-mail(s)'
            )

        cancelled = client.post(
            f'/api/reservations/{reservation_id}/annuler/'
        )
        self._check(
            'Annulation réservation',
            cancelled.status_code == 200,
            cancelled.data
        )

        reservation.refresh_from_db()
        reminder.refresh_from_db()
        self._check('Statut réservation annulé', reservation.statut == 'ANNULEE')
        self._check('Rappel annulé immédiatement', reminder.statut == 'ANNULE')

        planning_after_cancel = client.get('/api/planning/?date=2099-12-31')
        self._check(
            'Réservation annulée absente du planning',
            not any(
                item['id_reservation'] == reservation_id
                for item in planning_after_cancel.data
            )
        )
        self._check(
            'Seconde annulation refusée',
            client.post(
                f'/api/reservations/{reservation_id}/annuler/'
            ).status_code == 400
        )
        self._check(
            'Modification après annulation refusée',
            client.patch(
                f'/api/reservations/{reservation_id}/',
                {'notes': 'interdit'},
                format='json'
            ).status_code == 400
        )

        Token.objects.filter(user=django_user).delete()
        token = Token.objects.create(user=django_user)
        self._check(
            'Token DRF existant pour le compte RH',
            token is not None
        )
        token_client = APIClient()
        token_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self._check(
            'Token individuel Django autorisé pour un compte opérationnel',
            token_client.get('/api/salles/').status_code == 200
        )
