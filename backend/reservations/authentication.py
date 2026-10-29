from datetime import timedelta

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils import timezone

from .models import JetonAppareil, SessionRH

# L'activité est enregistrée au plus une fois par minute : pas d'écriture
# en base à chaque requête de l'API.
INTERVALLE_ACTIVITE = timedelta(seconds=60)


class RHSessionAuthentication(TokenAuthentication):
    """Authentifie un compte RH ET le profil choisi pour cette connexion."""

    def authenticate_credentials(self, key):
        try:
            session = SessionRH.objects.select_related(
                'utilisateur',
                'profil'
            ).get(key=key, actif=True, profil__actif=True)
        except SessionRH.DoesNotExist:
            # Laisse TokenAuthentication essayer le jeton par appareil.
            return None

        if not session.utilisateur.is_active:
            raise AuthenticationFailed("Compte utilisateur inactif.")
        max_age = getattr(settings, 'RH_SESSION_MAX_AGE', 8 * 60 * 60)
        maintenant = timezone.now()
        if (maintenant - session.derniere_activite).total_seconds() > max_age:
            session.actif = False
            session.save(update_fields=['actif'])
            raise AuthenticationFailed("Votre session RH a expiré.")
        if maintenant - session.derniere_activite > INTERVALLE_ACTIVITE:
            session.derniere_activite = maintenant
            session.save(update_fields=['derniere_activite'])
        return session.utilisateur, session


class ExpiringTokenAuthentication(TokenAuthentication):
    """Jeton par appareil (JetonAppareil), avec repli sur l'ancien Token DRF.

    Refuse les jetons trop anciens et ceux des comptes désactivés.
    """

    def authenticate_credentials(self, key):
        max_age = getattr(settings, 'TOKEN_MAX_AGE', 8 * 60 * 60)
        maintenant = timezone.now()

        jeton = JetonAppareil.objects.select_related('utilisateur').filter(key=key).first()
        if jeton is not None:
            if not jeton.utilisateur.is_active:
                raise AuthenticationFailed("Compte utilisateur inactif.")
            if (maintenant - jeton.derniere_activite).total_seconds() > max_age:
                jeton.delete()
                raise AuthenticationFailed("Votre session a expiré.")
            if maintenant - jeton.derniere_activite > INTERVALLE_ACTIVITE:
                jeton.derniere_activite = maintenant
                jeton.save(update_fields=['derniere_activite'])
            return jeton.utilisateur, jeton

        # Ancien Token DRF (comptes techniques créés par commande).
        user, token = super().authenticate_credentials(key)
        if not user.is_active:
            raise AuthenticationFailed("Compte utilisateur inactif.")
        if (maintenant - token.created).total_seconds() > max_age:
            token.delete()
            raise AuthenticationFailed("Votre session a expiré.")
        if maintenant - token.created > INTERVALLE_ACTIVITE:
            token.created = maintenant
            token.save(update_fields=['created'])
        return user, token


def request_rh_profile(request):
    auth = getattr(request, 'auth', None)
    profile = getattr(auth, 'profil', None)
    if profile:
        return profile
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        from .models import ProfilRH
        # La trace d'une action est rattachée à la personne, par son email.
        cle = (user.email or user.get_username()).strip().lower()[:100]
        libelle = (user.get_full_name().strip() or user.email or user.get_username())[:150]
        profile, cree = ProfilRH.objects.get_or_create(
            nom=cle, defaults={'actif': True, 'libelle': libelle}
        )
        if not cree and profile.libelle != libelle:
            profile.libelle = libelle
            profile.save(update_fields=['libelle'])
        return profile
    return None
