import logging
from threading import Thread

from django.core.mail import send_mail
from django.conf import settings


logger = logging.getLogger(__name__)


def envoyer_email_en_arriere_plan(callback):
    """Lance un envoi sans bloquer la réponse HTTP de l'utilisateur."""
    def run():
        try:
            callback()
        except Exception:
            logger.exception("Échec d'un envoi d'e-mail en arrière-plan.")

    Thread(target=run, name="uniserv-email", daemon=True).start()


def envoyer_email_acces_rh(user):
    prenom = user.first_name or user.username
    send_mail(
        subject="Votre accès – Gestion des salles de réunion UNISERV BTP",
        message=(
            f"Bonjour {prenom},\n\n"
            "Votre accès à la plateforme de gestion des salles de réunion "
            "UNISERV BTP a été créé.\n\n"
            f"Nom d'utilisateur :\n{user.username}\n\n"
            f"Lien de connexion :\n{settings.FRONTEND_URL.rstrip('/')}/login\n\n"
            "Utilisez le mot de passe RH communiqué par l'entreprise pour vous connecter.\n\n"
            "Cordialement,\n\nService Informatique\nUNISERV BTP"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


# ==========================================================
# CONFIRMATION D'UNE RESERVATION
# ==========================================================

def envoyer_confirmation_reservation(reservation, participants):

    liste_participants = ""

    if participants:
        for participant in participants:
            nom = participant.nom or "Participant"
            liste_participants += f"- {nom} ({participant.email})\n"
    else:
        liste_participants = "Aucun participant renseigné."

    sujet_demandeur = f"Confirmation de réservation - {reservation.objet}"

    message_demandeur = f"""
Bonjour {reservation.nom_demandeur},

Votre réservation de salle de réunion a été confirmée.

Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}
Nombre de participants : {reservation.nombre_participants}

Participants :
{liste_participants}

Cordialement,
Service RH
UNISERV BTP
"""

    send_mail(
        subject=sujet_demandeur,
        message=message_demandeur,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.email_demandeur],
        fail_silently=False,
    )

    for participant in participants:
        nom_participant = participant.nom or "Participant"

        sujet_participant = (
            f"Invitation à une réunion - {reservation.objet}"
        )

        message_participant = f"""
Bonjour {nom_participant},

Vous êtes invité à une réunion.

Demandeur : {reservation.nom_demandeur}
Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}

Cordialement,
Service RH
UNISERV BTP
"""

        send_mail(
            subject=sujet_participant,
            message=message_participant,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[participant.email],
            fail_silently=False,
        )


# ==========================================================
# ANNULATION D'UNE RESERVATION
# ==========================================================

def envoyer_annulation_reservation(reservation, participants):

    sujet_demandeur = f"Annulation de réservation - {reservation.objet}"

    message_demandeur = f"""
Bonjour {reservation.nom_demandeur},

Votre réservation de salle de réunion a été annulée.

Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}

Cordialement,
Service RH
UNISERV BTP
"""

    send_mail(
        subject=sujet_demandeur,
        message=message_demandeur,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.email_demandeur],
        fail_silently=False,
    )

    for participant in participants:
        nom_participant = participant.nom or "Participant"

        sujet_participant = f"Réunion annulée - {reservation.objet}"

        message_participant = f"""
Bonjour {nom_participant},

La réunion à laquelle vous étiez invité a été annulée.

Demandeur : {reservation.nom_demandeur}
Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}

Cordialement,
Service RH
UNISERV BTP
"""

        send_mail(
            subject=sujet_participant,
            message=message_participant,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[participant.email],
            fail_silently=False,
        )


# ==========================================================
# MODIFICATION D'UNE RESERVATION
# ==========================================================

def envoyer_modification_reservation(reservation, participants):

    liste_participants = ""

    if participants:
        for participant in participants:
            nom = participant.nom or "Participant"
            liste_participants += f"- {nom} ({participant.email})\n"
    else:
        liste_participants = "Aucun participant renseigné."

    sujet_demandeur = f"Modification de réservation - {reservation.objet}"

    message_demandeur = f"""
Bonjour {reservation.nom_demandeur},

Votre réservation de salle de réunion a été modifiée.

Nouvelles informations :

Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}
Nombre de participants : {reservation.nombre_participants}

Participants :
{liste_participants}

Cordialement,
Service RH
UNISERV BTP
"""

    send_mail(
        subject=sujet_demandeur,
        message=message_demandeur,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.email_demandeur],
        fail_silently=False,
    )

    for participant in participants:
        nom_participant = participant.nom or "Participant"

        sujet_participant = (
            f"Modification de réunion - {reservation.objet}"
        )

        message_participant = f"""
Bonjour {nom_participant},

La réunion à laquelle vous êtes invité a été modifiée.

Demandeur : {reservation.nom_demandeur}
Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}

Cordialement,
Service RH
UNISERV BTP
"""

        send_mail(
            subject=sujet_participant,
            message=message_participant,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[participant.email],
            fail_silently=False,
        )


# ==========================================================
# RAPPEL 2 HEURES AVANT LA REUNION
# ==========================================================

def envoyer_rappel_reservation(reservation, participants):

    sujet_demandeur = f"Rappel de réunion - {reservation.objet}"

    message_demandeur = f"""
Bonjour {reservation.nom_demandeur},

Nous vous rappelons que votre réunion est prévue dans 2 heures.

Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}

Cordialement,
Service RH
UNISERV BTP
"""

    send_mail(
        subject=sujet_demandeur,
        message=message_demandeur,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.email_demandeur],
        fail_silently=False,
    )

    for participant in participants:
        nom_participant = participant.nom or "Participant"

        sujet_participant = (
            f"Rappel de réunion - {reservation.objet}"
        )

        message_participant = f"""
Bonjour {nom_participant},

Nous vous rappelons que la réunion à laquelle vous êtes invité
est prévue dans 2 heures.

Demandeur : {reservation.nom_demandeur}
Salle : {reservation.id_salle.nom_salle}
Date : {reservation.date_reservation}
Heure : {reservation.heure_debut} - {reservation.heure_fin}
Objet : {reservation.objet}

Cordialement,
Service RH
UNISERV BTP
"""

        send_mail(
            subject=sujet_participant,
            message=message_participant,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[participant.email],
            fail_silently=False,
        )
