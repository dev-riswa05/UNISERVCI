from django.db import models


from django.conf import settings
from django.core.validators import FileExtensionValidator
import secrets


def generate_session_key():
    return secrets.token_hex(20)


class ProfilUtilisateur(models.Model):
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil_application'
    )
    photo = models.FileField(
        upload_to='profils/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profil_utilisateur'

    def __str__(self):
        return f"Profil de {self.utilisateur}"


class ProfilRH(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'profil_rh'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class SessionRH(models.Model):
    key = models.CharField(
        primary_key=True,
        max_length=40,
        default=generate_session_key,
        editable=False
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions_rh'
    )
    profil = models.ForeignKey(
        ProfilRH,
        on_delete=models.PROTECT,
        related_name='sessions'
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_activite = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'session_rh'

    def __str__(self):
        return f"{self.utilisateur} — {self.profil}"


class Utilisateurs(models.Model):
    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)
    mot_de_passe = models.CharField(max_length=255)
    role = models.CharField(max_length=50, blank=True, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'utilisateurs'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.nom} {self.prenom or ''}".strip()


class Salles(models.Model):
    id_salle = models.AutoField(primary_key=True)
    nom_salle = models.CharField(max_length=100)
    localisation = models.CharField(max_length=150, blank=True, null=True)
    etage = models.CharField(max_length=50, blank=True, null=True)
    capacite = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'salles'
        verbose_name = "Salle"
        verbose_name_plural = "Salles"

    def __str__(self):
        return self.nom_salle


class Reservations(models.Model):
    id_reservation = models.AutoField(primary_key=True)

    id_salle = models.ForeignKey(
        Salles,
        on_delete=models.PROTECT,
        db_column='id_salle'
    )

    id_utilisateur = models.ForeignKey(
        Utilisateurs,
        on_delete=models.PROTECT,
        db_column='id_utilisateur'
    )

    nom_demandeur = models.CharField(max_length=150)
    email_demandeur = models.CharField(max_length=150)
    objet = models.CharField(max_length=255)
    date_reservation = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    nombre_participants = models.IntegerField(blank=True, null=True)
    statut = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(blank=True, null=True)
    date_modification = models.DateTimeField(blank=True, null=True)

    # Colonnes ajoutées à la table MySQL historique par migration SQL.
    created_by = models.ForeignKey(
        ProfilRH,
        on_delete=models.PROTECT,
        db_column='created_by_id',
        related_name='reservations_creees',
        blank=True,
        null=True,
        db_constraint=False
    )
    created_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        ProfilRH,
        on_delete=models.PROTECT,
        db_column='updated_by_id',
        related_name='reservations_modifiees',
        blank=True,
        null=True,
        db_constraint=False
    )
    updated_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.ForeignKey(
        ProfilRH,
        on_delete=models.PROTECT,
        db_column='cancelled_by_id',
        related_name='reservations_annulees',
        blank=True,
        null=True,
        db_constraint=False
    )
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reservations'
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"

    def __str__(self):
        return f"{self.objet} - {self.date_reservation}"


class Participants(models.Model):
    id_participant = models.AutoField(primary_key=True)

    id_reservation = models.ForeignKey(
        Reservations,
        on_delete=models.CASCADE,
        db_column='id_reservation'
    )

    nom = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'participants'
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

    def __str__(self):
        return self.email


class Rappels(models.Model):
    id_rappel = models.AutoField(primary_key=True)

    id_reservation = models.ForeignKey(
        Reservations,
        on_delete=models.CASCADE,
        db_column='id_reservation'
    )

    date_heure_prevue = models.DateTimeField()
    statut = models.CharField(max_length=50, blank=True, null=True)
    date_heure_envoi = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rappels'
        verbose_name = "Rappel"
        verbose_name_plural = "Rappels"

    def __str__(self):
        return f"Rappel #{self.id_rappel}"


class Notifications(models.Model):
    id_notification = models.AutoField(primary_key=True)

    id_reservation = models.ForeignKey(
        Reservations,
        on_delete=models.CASCADE,
        db_column='id_reservation'
    )

    destinataire = models.CharField(max_length=150)
    type_notification = models.CharField(max_length=50)
    objet = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(max_length=50, blank=True, null=True)
    date_envoi = models.DateTimeField(blank=True, null=True)
    message_erreur = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notifications'
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.type_notification} - {self.destinataire}"


class Parametres(models.Model):
    id_parametre = models.AutoField(primary_key=True)
    cle = models.CharField(unique=True, max_length=100)
    valeur = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'parametres'
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"

    def __str__(self):
        return self.cle
