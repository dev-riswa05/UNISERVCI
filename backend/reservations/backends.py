from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Connexion par adresse email, sans tenir compte des majuscules.

    L'email est l'identifiant personnel de chaque compte. Le nom d'utilisateur
    Django reste utilisable en interne (administration Django, commandes).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (kwargs.get('email') or username or '').strip()
        if not email or password is None:
            return None
        model = get_user_model()
        # Un email ne doit correspondre qu'à un seul compte : en cas de doublon
        # historique, on refuse plutôt que de deviner.
        candidats = list(model.objects.filter(email__iexact=email)[:2])
        if len(candidats) != 1:
            # Mime le coût d'un hachage pour ne pas révéler si l'email existe.
            model().set_password(password)
            return None
        user = candidats[0]
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
