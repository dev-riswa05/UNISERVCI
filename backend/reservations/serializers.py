from datetime import datetime, time, timedelta

from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from .models import (
    Salles,
    Reservations,
    Participants,
    Rappels,
)

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
    """Version tablette d'une salle, sans champs techniques inutiles."""

    class Meta:
        model = Salles
        fields = ['id_salle', 'nom_salle']


# ==========================================================
# PARTICIPANTS
# ==========================================================

class ParticipantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Participants
        fields = ['nom', 'email']


# ==========================================================
# RESERVATIONS
# ==========================================================

class ReservationSerializer(serializers.ModelSerializer):

    created_by_name = serializers.CharField(source='created_by.nom', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.nom', read_only=True)
    cancelled_by_name = serializers.CharField(source='cancelled_by.nom', read_only=True)
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

    class Meta:
        model = Reservations

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

    def get_notification_status(self, reservation):
        from .models import Notifications
        statuses = list(Notifications.objects.filter(
            id_reservation=reservation
        ).values_list('statut', flat=True))
        if not statuses:
            return 'NON_SUIVIE'
        if any(value == 'ECHEC' for value in statuses):
            return 'ECHEC'
        if all(value == 'ENVOYEE' for value in statuses):
            return 'ENVOYEE'
        return 'EN_ATTENTE'

        # Ces valeurs sont imposées par le serveur. Un client ne doit pas
        # pouvoir attribuer une réservation à un autre RH ni forcer son statut.
        read_only_fields = [
            'id_reservation',
            'id_utilisateur',
            'statut', 'created_at', 'updated_at', 'cancelled_at',
        ]


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
        ouverture = time(8, 0)
        fermeture = time(17, 30)

        if debut < ouverture or fin > fermeture:
            raise serializers.ValidationError(
                "Le créneau doit être compris entre 08h00 et 17h30."
            )

        # Vérification de l'ordre des horaires
        if debut >= fin:
            raise serializers.ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )


        # Vérification des conflits
        conflit = Reservations.objects.filter(
            id_salle=salle,
            date_reservation=date,
            heure_debut__lt=fin,
            heure_fin__gt=debut,
        ).exclude(
            statut='ANNULEE'
        )


        # En modification, on exclut la réservation actuelle
        if self.instance:

            conflit = conflit.exclude(
                id_reservation=self.instance.id_reservation
            )


        if conflit.exists():
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

    # Noms lisibles utilisés dans l'historique sans exposer les sessions.
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
