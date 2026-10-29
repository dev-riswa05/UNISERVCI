from rest_framework.permissions import BasePermission

RH_GROUP = "RH"
SUPER_ADMIN_GROUP = "SUPER_ADMIN"
MANAGER_GROUP = "MANAGER"

# Rôles pouvant être attribués à un compte créé depuis l'administration.
ROLES_COMPTES = (RH_GROUP, MANAGER_GROUP)


def user_role(user):
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if user.is_superuser or user.groups.filter(name=SUPER_ADMIN_GROUP).exists():
        return SUPER_ADMIN_GROUP
    if user.groups.filter(name=RH_GROUP).exists():
        return RH_GROUP
    if user.groups.filter(name=MANAGER_GROUP).exists():
        return MANAGER_GROUP
    return None


def cle_personne(user):
    """Clé de traçabilité d'une personne : son email en minuscules."""
    return (user.email or user.get_username()).strip().lower()[:100]


def est_proprietaire(user, reservation):
    """Vrai si la réservation a été créée par cette personne."""
    createur = getattr(reservation, 'created_by', None)
    return createur is not None and createur.nom == cle_personne(user)


def gere_toutes_les_reservations(user):
    """Super Admin et RH gèrent toutes les réservations ; un manager, les siennes."""
    return user_role(user) in {SUPER_ADMIN_GROUP, RH_GROUP}


class IsRH(BasePermission):
    message = "Cette opération est réservée au service RH."
    def has_permission(self, request, view):
        return user_role(request.user) in {SUPER_ADMIN_GROUP, RH_GROUP}

class IsSuperAdmin(BasePermission):
    message = "Cette opération est réservée au Super Administrateur."
    def has_permission(self, request, view):
        return user_role(request.user) == SUPER_ADMIN_GROUP

class IsRHOrManager(BasePermission):
    message = "Cette opération n'est pas autorisée pour ce compte."
    def has_permission(self, request, view):
        return user_role(request.user) in {SUPER_ADMIN_GROUP, RH_GROUP, MANAGER_GROUP}
