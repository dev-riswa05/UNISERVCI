import uuid
from datetime import timedelta

from django.conf import settings

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from .models import JetonAppareil, ProfilUtilisateur, SessionRH
from .permissions import SUPER_ADMIN_GROUP, user_role


JPEG_MAGIC = bytes([0xFF, 0xD8, 0xFF])
PNG_MAGIC = bytes([0x89]) + b'PNG' + bytes([0x0D, 0x0A, 0x1A, 0x0A])


def current_user_payload(request):
    user = request.user
    profile = ProfilUtilisateur.objects.filter(utilisateur=user).first()
    photo_url = request.build_absolute_uri(profile.photo.url) if profile and profile.photo else None
    return {"id": user.pk, "username": user.username, "email": user.email,
            "first_name": user.first_name, "last_name": user.last_name,
            "role": user_role(user), "is_active": user.is_active,
            "photo_url": photo_url}

class LoginThrottle(AnonRateThrottle):
    scope = "login"


class LoginUserThrottle(SimpleRateThrottle):
    """Limite les essais par nom d'utilisateur, quelle que soit l'adresse IP."""
    scope = "login_user"

    def get_cache_key(self, request, view):
        email = str(request.data.get("email") or "").strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class PasswordThrottle(UserRateThrottle):
    scope = "password"

class RoleLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle, LoginUserThrottle]

    def get_authenticate_header(self, request):
        # Un échec de connexion répond 401 (et non 403).
        return 'Token'

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""
        if not email or not password:
            raise AuthenticationFailed("Adresse email et mot de passe requis.")
        user = authenticate(request, email=email, password=password)
        # Message unique : ne révèle ni l'existence, ni l'état, ni les droits
        # d'un compte. Le rôle est lu côté serveur : l'utilisateur n'a pas à
        # dire qui il est, l'application le redirige selon son profil.
        role = user_role(user) if user is not None else None
        if user is None or not user.is_active or not role:
            raise AuthenticationFailed("Identifiants incorrects.")
        # Un jeton par connexion : se connecter sur un appareil ne déconnecte
        # pas les autres, et se déconnecter ne révoque que cet appareil.
        maintenant = timezone.now()
        limite = maintenant - timedelta(seconds=settings.TOKEN_MAX_AGE)
        JetonAppareil.objects.filter(utilisateur=user, derniere_activite__lt=limite).delete()
        token = JetonAppareil.objects.create(utilisateur=user, derniere_activite=maintenant)
        return Response({"token": token.key, "role": role, "username": user.username,
                         "email": user.email, "name": user.get_full_name() or user.username})

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(current_user_payload(request))
    def patch(self, request):
        if user_role(request.user) != SUPER_ADMIN_GROUP:
            raise PermissionDenied("Les informations du compte RH sont en lecture seule.")
        user = request.user
        username = (request.data.get("username") or user.username).strip()
        email = (request.data.get("email") or user.email).strip().lower()
        try:
            validate_email(email)
        except DjangoValidationError:
            raise ValidationError({"email": "Saisissez une adresse email valide."})
        others = get_user_model().objects.exclude(pk=user.pk)
        if others.filter(username__iexact=username).exists():
            raise ValidationError({"username": "Ce nom d'utilisateur est déjà utilisé."})
        if others.filter(email__iexact=email).exists():
            raise ValidationError({"email": "Cette adresse email est déjà utilisée."})
        user.username, user.email = username, email
        user.save(update_fields=["username", "email"])
        return self.get(request)


class ProfilePhotoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        photo = request.FILES.get('photo')
        if not photo:
            raise ValidationError({'photo': 'Sélectionnez une photo.'})
        if photo.size > 2 * 1024 * 1024:
            raise ValidationError({'photo': 'La photo ne doit pas dépasser 2 Mo.'})
        if photo.content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
            raise ValidationError({'photo': 'Formats autorisés : JPG, PNG ou WEBP.'})
        entete = photo.read(12)
        photo.seek(0)
        if entete.startswith(JPEG_MAGIC):
            extension = 'jpg'
        elif entete.startswith(PNG_MAGIC):
            extension = 'png'
        elif entete[:4] == b'RIFF' and entete[8:12] == b'WEBP':
            extension = 'webp'
        else:
            raise ValidationError({'photo': "Le fichier n'est pas une image valide."})
        photo.name = f"{uuid.uuid4().hex}.{extension}"
        profile, _ = ProfilUtilisateur.objects.get_or_create(utilisateur=request.user)
        if profile.photo:
            profile.photo.delete(save=False)
        profile.photo = photo
        profile.full_clean()
        profile.save()
        return Response(current_user_payload(request))

    def delete(self, request):
        profile = ProfilUtilisateur.objects.filter(utilisateur=request.user).first()
        if profile and profile.photo:
            profile.photo.delete(save=False)
            profile.photo = None
            profile.save(update_fields=['photo', 'date_modification'])
        return Response(current_user_payload(request))

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PasswordThrottle]
    def post(self, request):
        if user_role(request.user) != SUPER_ADMIN_GROUP:
            raise PermissionDenied("Le compte RH est géré par le Super Administrateur.")
        current, new = request.data.get("current_password") or "", request.data.get("new_password") or ""
        if not request.user.check_password(current):
            raise ValidationError({"current_password": "Le mot de passe actuel est incorrect."})
        if new != (request.data.get("confirmation") or ""):
            raise ValidationError({"confirmation": "Les nouveaux mots de passe ne correspondent pas."})
        try:
            validate_password(new, request.user)
        except DjangoValidationError as exc:
            raise ValidationError({"new_password": list(exc.messages)})
        request.user.set_password(new); request.user.save(update_fields=["password"])
        Token.objects.filter(user=request.user).delete()
        request.user.jetons_appareil.all().delete()
        request.user.sessions_rh.filter(actif=True).update(actif=False)
        return Response({"message": "Mot de passe modifié. Veuillez vous reconnecter."})

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if isinstance(request.auth, SessionRH):
            request.auth.actif = False; request.auth.save(update_fields=["actif"])
        elif isinstance(request.auth, JetonAppareil):
            request.auth.delete()  # seul cet appareil est déconnecté
        else:
            Token.objects.filter(user=request.user).delete()
        return Response({"message": "Session fermée."})
