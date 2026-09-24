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
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import ProfilUtilisateur, SessionRH
from .permissions import SUPER_ADMIN_GROUP, user_role


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

class RoleLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        requested_role = (request.data.get("role") or "").upper()
        email = (request.data.get("email") or "").strip()
        if not username or not password:
            raise AuthenticationFailed("Nom d'utilisateur et mot de passe requis.")
        user = authenticate(request, username=username, password=password)
        if user is None:
            raise AuthenticationFailed("Identifiants incorrects.")
        if not user.is_active:
            raise AuthenticationFailed("Ce compte est inactif.")
        role = user_role(user)
        if not role:
            raise PermissionDenied("Ce compte n'a aucun rôle applicatif.")
        if requested_role and role != requested_role:
            raise PermissionDenied("Ce compte n'est pas autorisé dans cet espace.")
        if role == SUPER_ADMIN_GROUP and (not email or user.email.lower() != email.lower()):
            raise AuthenticationFailed("Email, nom d'utilisateur ou mot de passe incorrect.")
        # Un nouveau login du même compte ne doit pas déconnecter une autre
        # page déjà ouverte. Le token utilisateur est réutilisé et réactivé.
        token, _ = Token.objects.get_or_create(user=user)
        token.created = timezone.now()
        token.save(update_fields=['created'])
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
        return Response({"message": "Mot de passe modifié. Veuillez vous reconnecter."})

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if isinstance(request.auth, SessionRH):
            request.auth.actif = False; request.auth.save(update_fields=["actif"])
        else:
            Token.objects.filter(user=request.user).delete()
        return Response({"message": "Session fermée."})
