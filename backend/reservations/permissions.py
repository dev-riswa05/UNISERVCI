from rest_framework.permissions import BasePermission

DISPLAY_GROUP = "AFFICHAGE"
RH_GROUP = "RH"
SUPER_ADMIN_GROUP = "SUPER_ADMIN"

def user_role(user):
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if user.is_superuser or user.groups.filter(name=SUPER_ADMIN_GROUP).exists():
        return SUPER_ADMIN_GROUP
    if user.groups.filter(name=RH_GROUP).exists():
        return RH_GROUP
    if user.groups.filter(name=DISPLAY_GROUP).exists():
        return DISPLAY_GROUP
    return None

class IsRH(BasePermission):
    message = "Cette opération est réservée au service RH."
    def has_permission(self, request, view):
        return user_role(request.user) in {SUPER_ADMIN_GROUP, RH_GROUP}

class IsSuperAdmin(BasePermission):
    message = "Cette opération est réservée au Super Administrateur."
    def has_permission(self, request, view):
        return user_role(request.user) == SUPER_ADMIN_GROUP

class IsRHOrDisplay(BasePermission):
    message = "Ce compte n'est pas autorisé à consulter l'affichage des salles."
    def has_permission(self, request, view):
        return user_role(request.user) in {SUPER_ADMIN_GROUP, RH_GROUP, DISPLAY_GROUP}
