from datetime import datetime, timedelta

from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from .models import (
    Salles,
    Reservations,
    Participants,
    Rappels,
)

from .horaires import FERMETURE, OUVERTURE
from .permissions import MANAGER_GROUP, est_proprietaire, user_role
from .emails import (
    envoyer_confirmation_reservation,
    envoyer_modification_reservation,
)


# ==========================================================
# SALLES
# ==========================================================

class SalleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Salles
        fields = '__all__'


class AffichageSalleSerializer(serializers.ModelSerializer):
    """Version écran d'une salle, sans champs techniques inutiles."""

    class Meta:
        model = Salles
        fields = ['id_salle', 'nom_salle', 'etage', 'localisation']


# ==========================================================
# PARTICIPANTS
# ==========================================================

class ParticipantSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = Participants
        fields = ['nom', 'email']


MAX_PARTICIPANTS = 100


def reservations_en_conflit(salle, date, debut, fin, exclure=None):
    """Réservations actives de la salle qui chevauchent le créneau demandé."""
    conflit = Reservations.objects.filter(
        id_salle=salle,
        date_reservation=date,
        heure_debut__lt=fin,
        heure_fin__gt=debut,
    ).exclude(statut='ANNULEE')
    if exclure is not None:
        conflit = conflit.exclude(id_reservation=exclure)
    return conflit


def verrouiller_et_verifier(salle, date, debut, fin, exclure=None):
    """Sérialise les réservations d'une même salle puis revérifie le conflit.

    Le verrou sur la ligne de la salle empêche deux requêtes simultanées de
    passer toutes deux le contrôle de validate() avant l'insertion.
    Doit être appelé dans une transaction.
    """
    Salles.objects.select_for_update().get(pk=salle.pk)
    if reservations_en_conflit(salle, date, debut, fin, exclure).exists():
        raise serializers.ValidationError(
            "Cette salle est déjà réservée sur ce créneau."
        )


# ==========================================================
# RESERVATIONS
# ==========================================================

class ReservationSerializer(serializers.ModelSerializer):

    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    cancelled_by_name = serializers.SerializerMethodField()
    notification_status = serializers.SerializerMethodField()

    participants = ParticipantSerializer(
        many=True,
        required=False,
        source='participants_set'
    )

    salle_nom = serializers.CharField(
        source='id_salle.nom_salle',
        read_only=True
    )

    email_demandeur = serializers.EmailField(max_length=255)

    class Meta:
        model = Reservations
        extra_kwargs = {
            'nombre_participants': {'min_value': 1},
        }

        fields = [
            'id_reservation',
            'id_salle',
            'salle_nom',
            'id_utilisateur',
            'nom_demandeur',
            'email_demandeur',
            'objet',
            'date_reservation',
            'heure_debut',
            'heure_fin',
            'nombre_participants',
            'statut',
            'notes',
            'participants',
            'created_by_name', 'created_at',
            'updated_by_name', 'updated_at',
            'cancelled_by_name', 'cancelled_at',
            'notification_status',
        ]
        read_only_fields = [
            'id_reservation', 'id_utilisateur', 'statut',
            'created_at', 'updated_at', 'cancelled_at',
        ]

    def to_representation(self, instance):
        """Un manager voit ses réservations en détail, celles des autres seulement
        comme un créneau occupé (sans objet, participants, ni coordonnées)."""
        # Le rôle est calculé une seule fois par requête (et non par réservation).
        if not hasattr(self, '_acteur'):
            user = getattr(self.context.get('request'), 'user', None)
            self._acteur = (
                user, user_role(user) if user is not None else None
            )
        user, role = self._acteur
        if role == MANAGER_GROUP and not est_proprietaire(user, instance):
            return {
                'id_reservation': instance.id_reservation,
                'id_salle': instance.id_salle_id,
                'salle_nom': instance.id_salle.nom_salle,
                'date_reservation': instance.date_reservation,
                'heure_debut': instance.heure_debut,
                'heure_fin': instance.heure_fin,
                'statut': instance.statut,
                'objet': 'Réservé',
                'lecture_seule': True,
            }
        data = super().to_representation(instance)
        data['lecture_seule'] = False
        return data

    @staticmethod
    def _nom_profil(profil):
        # Nom complet de la personne, sinon son email.
        return (profil.libelle or profil.nom) if profil else None

    def get_created_by_name(self, reservation):
        return self._nom_profil(reservation.created_by)

    def get_updated_by_name(self, reservation):
        return self._nom_profil(reservation.updated_by)

    def get_cancelled_by_name(self, reservation):
        return self._nom_profil(reservation.cancelled_by)

    def get_notification_status(self, reservation):
        # notifications_set est préchargé par les vues de liste (pas de
        # requête par réservation) ; sinon Django l'interroge à la demande.
        statuses = [n.statut for n in reservation.notifications_set.all()]
        if not statuses:
            return 'NON_SUIVIE'
        if any(value == 'ECHEC' for value in statuses):
            return 'ECHEC'
        if all(value == 'ENVOYEE' for value in statuses):
            return 'ENVOYEE'
        return 'EN_ATTENTE'


    # ======================================================
    # VERIFICATION DES CONFLITS
    # ======================================================

    def validate(self, data):

        # Modification PATCH / PUT
        if self.instance:

            salle = data.get(
                'id_salle',
                self.instance.id_salle
            )

            date = data.get(
                'date_reservation',
                self.instance.date_reservation
            )

            debut = data.get(
                'heure_debut',
                self.instance.heure_debut
            )

            fin = data.get(
                'heure_fin',
                self.instance.heure_fin
            )

        # Création POST
        else:

            salle = data.get('id_salle')
            date = data.get('date_reservation')
            debut = data.get('heure_debut')
            fin = data.get('heure_fin')

        if salle and not salle.active:
            raise serializers.ValidationError({
                'id_salle': "Cette salle est inactive et ne peut pas être réservée."
            })

        nombre_participants = data.get(
            'nombre_participants',
            getattr(self.instance, 'nombre_participants', None)
        )
        if (
            salle
            and salle.capacite is not None
            and nombre_participants is not None
            and nombre_participants > salle.capacite
        ):
            raise serializers.ValidationError({
                'nombre_participants': (
                    f"Cette salle accepte au maximum {salle.capacite} participants."
                )
            })


        # Les salles ne peuvent être réservées que pendant les horaires
        # d'ouverture. Les bornes 08h00 et 17h30 sont incluses.
        if debut < OUVERTURE or fin > FERMETURE:
            raise serializers.ValidationError(
                "Le créneau doit être compris entre 08h00 et 17h30."
            )

        # Vérification de l'ordre des horaires
        if debut >= fin:
            raise serializers.ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )


        # Interdit de réserver dans le passé (à la création, ou si le créneau
        # est déplacé ; modifier les notes d'une réunion en cours reste permis).
        creneau_modifie = (
            self.instance is None
            or date != self.instance.date_reservation
            or debut != self.instance.heure_debut
        )
        if creneau_modifie:
            maintenant = timezone.localtime()
            if date < maintenant.date() or (
                date == maintenant.date() and debut < maintenant.time()
            ):
                raise serializers.ValidationError(
                    "Le créneau demandé est déjà passé."
                )

        participants = self.initial_data.get('participants')
        if isinstance(participants, list) and len(participants) > MAX_PARTICIPANTS:
            raise serializers.ValidationError({
                'participants': f"Maximum {MAX_PARTICIPANTS} participants."
            })

        # Contrôle rapide pour un message clair ; le contrôle définitif,
        # verrouillé, est refait dans create() / update().
        exclure = self.instance.id_reservation if self.instance else None
        if reservations_en_conflit(salle, date, debut, fin, exclure).exists():
            raise serializers.ValidationError(
                "Cette salle est déjà réservée sur ce créneau."
            )

        return data


    # ======================================================
    # CREATION
    # ======================================================

    @transaction.atomic
    def create(self, validated_data):

        participants_data = validated_data.pop(
            'participants_set',
            []
        )


        verrouiller_et_verifier(
            validated_data['id_salle'],
            validated_data['date_reservation'],
            validated_data['heure_debut'],
            validated_data['heure_fin'],
        )

        # Création de la réservation
        reservation = Reservations.objects.create(
            **validated_data
        )


        # ==================================================
        # CREATION AUTOMATIQUE DU RAPPEL H-2
        # ==================================================

        date_heure_reunion = datetime.combine(
            reservation.date_reservation,
            reservation.heure_debut
        )

        if timezone.is_naive(date_heure_reunion):
            date_heure_reunion = timezone.make_aware(
                date_heure_reunion
            )

        date_heure_rappel = (
            date_heure_reunion - timedelta(hours=2)
        )

        Rappels.objects.create(
            id_reservation=reservation,
            date_heure_prevue=date_heure_rappel,
            statut='EN_ATTENTE',
            date_heure_envoi=None
        )


        # ==================================================
        # CREATION DES PARTICIPANTS
        # ==================================================

        participants_crees = []

        for participant_data in participants_data:

            participant = Participants.objects.create(
                id_reservation=reservation,
                **participant_data
            )

            participants_crees.append(participant)


        # ==================================================
        # EMAILS DE CONFIRMATION
        # ==================================================

        # La réponse API ne doit pas devenir une erreur si le SMTP tombe après
        # l'enregistrement. L'envoi n'est déclenché qu'après le COMMIT MySQL.
        transaction.on_commit(
            lambda: envoyer_confirmation_reservation(
                reservation,
                participants_crees
            ),
            robust=True
        )


        return reservation


    # ======================================================
    # MODIFICATION
    # ======================================================

    @transaction.atomic
    def update(self, instance, validated_data):

        participants_data = validated_data.pop(
            'participants_set',
            None
        )


        instance = Reservations.objects.select_for_update().get(
            pk=instance.pk
        )
        if instance.statut == 'ANNULEE':
            raise serializers.ValidationError(
                "Une réservation annulée ne peut plus être modifiée."
            )
        verrouiller_et_verifier(
            validated_data.get('id_salle', instance.id_salle),
            validated_data.get('date_reservation', instance.date_reservation),
            validated_data.get('heure_debut', instance.heure_debut),
            validated_data.get('heure_fin', instance.heure_fin),
            exclure=instance.id_reservation,
        )

        # Mise à jour des informations
        for attribut, valeur in validated_data.items():
            setattr(
                instance,
                attribut,
                valeur
            )

        instance.save()


        # ==================================================
        # MISE A JOUR DU RAPPEL H-2
        # ==================================================

        date_heure_reunion = datetime.combine(
            instance.date_reservation,
            instance.heure_debut
        )

        if timezone.is_naive(date_heure_reunion):
            date_heure_reunion = timezone.make_aware(
                date_heure_reunion
            )

        date_heure_rappel = (
            date_heure_reunion - timedelta(hours=2)
        )

        rappel = Rappels.objects.filter(
            id_reservation=instance
        ).first()

        if rappel:
            rappel.date_heure_prevue = date_heure_rappel
            rappel.statut = 'EN_ATTENTE'
            rappel.date_heure_envoi = None
            rappel.save()

        else:
            Rappels.objects.create(
                id_reservation=instance,
                date_heure_prevue=date_heure_rappel,
                statut='EN_ATTENTE',
                date_heure_envoi=None
            )


        # ==================================================
        # MISE A JOUR DES PARTICIPANTS
        # ==================================================

        if participants_data is not None:

            Participants.objects.filter(
                id_reservation=instance
            ).delete()

            for participant_data in participants_data:

                Participants.objects.create(
                    id_reservation=instance,
                    **participant_data
                )


        participants = Participants.objects.filter(
            id_reservation=instance
        )


        # ==================================================
        # EMAILS DE MODIFICATION
        # ==================================================

        participant_ids = list(
            participants.values_list('id_participant', flat=True)
        )

        transaction.on_commit(
            lambda: envoyer_modification_reservation(
                instance,
                Participants.objects.filter(
                    id_participant__in=participant_ids
                )
            ),
            robust=True
        )


        return instance


class AffichageReservationSerializer(serializers.ModelSerializer):
    """Données non sensibles autorisées sur les écrans placés devant les salles."""

    salle_nom = serializers.CharField(
        source='id_salle.nom_salle',
        read_only=True
    )

    # Page publique : l'objet réel d'une réunion peut être confidentiel.
    objet = serializers.SerializerMethodField()

    def get_objet(self, reservation):
        return 'Réunion'

    class Meta:
        model = Reservations
        fields = [
            'id_reservation',
            'id_salle',
            'salle_nom',
            'objet',
            'date_reservation',
            'heure_debut',
            'heure_fin',
        ]
        read_only_fields = fields
