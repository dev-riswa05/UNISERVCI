from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils import timezone

from .models import SessionRH


class RHSessionAuthentication(TokenAuthentication):
    """Authentifie un compte RH ET le profil choisi pour cette connexion."""

    def authenticate_credentials(self, key):
        try:
            session = SessionRH.objects.select_related(
                'utilisateur',
                'profil'
            ).get(key=key, actif=True, profil__actif=True)
        except SessionRH.DoesNotExist:
            # Laisse TokenAuthentication essayer le token technique AFFICHAGE.
            return None

        if not session.utilisateur.is_active:
            raise AuthenticationFailed("Compte utilisateur inactif.")
        max_age = getattr(settings, 'RH_SESSION_MAX_AGE', 8 * 60 * 60)
        if (timezone.now() - session.derniere_activite).total_seconds() > max_age:
            session.actif = False
            session.save(update_fields=['actif'])
            raise AuthenticationFailed("Votre session RH a expiré.")
        # auto_now n'est pas déclenché par une simple lecture : cette mise à
        # jour prolonge uniquement une session réellement utilisée.
        session.derniere_activite = timezone.now()
        session.save(update_fields=['derniere_activite'])
        return session.utilisateur, session


class ExpiringTokenAuthentication(TokenAuthentication):
    """Refuse les tokens trop anciens et ceux des comptes désactivés."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if not user.is_active:
            raise AuthenticationFailed("Compte utilisateur inactif.")
        max_age = getattr(settings, 'TOKEN_MAX_AGE', 8 * 60 * 60)
        if (timezone.now() - token.created).total_seconds() > max_age:
            token.delete()
            raise AuthenticationFailed("Votre session a expiré.")
        token.created = timezone.now()
        token.save(update_fields=['created'])
        return user, token


def request_rh_profile(request):
    auth = getattr(request, 'auth', None)
    profile = getattr(auth, 'profil', None)
    if profile:
        return profile
    if request.user and request.user.is_authenticated:
        from .models import ProfilRH
        profile, _ = ProfilRH.objects.get_or_create(
            nom=request.user.get_username().upper(), defaults={'actif': True}
        )
        return profile
    return None
