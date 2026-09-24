from django.contrib import admin
from .models import (
    Utilisateurs,
    Salles,
    Reservations,
    Participants,
    Rappels,
    Notifications,
    Parametres,
    ProfilRH,
    SessionRH,
    ProfilUtilisateur,
)

admin.site.register(Utilisateurs)
admin.site.register(Salles)
admin.site.register(Reservations)
admin.site.register(Participants)
admin.site.register(Rappels)
admin.site.register(Notifications)
admin.site.register(Parametres)
admin.site.register(ProfilRH)
admin.site.register(SessionRH)
admin.site.register(ProfilUtilisateur)
