import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from reservations.permissions import MANAGER_GROUP, RH_GROUP, SUPER_ADMIN_GROUP

ROLES = (SUPER_ADMIN_GROUP, RH_GROUP, MANAGER_GROUP)


class Command(BaseCommand):
    help = (
        "Crée ou met à jour un compte (Super Admin, RH ou Manager). "
        "L'email est l'identifiant de connexion ; le mot de passe est saisi de "
        "façon masquée ou lu dans la variable COMPTE_PASSWORD."
    )

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--role', default=RH_GROUP, choices=ROLES)
        parser.add_argument('--prenom', default='')
        parser.add_argument('--nom', default='')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise CommandError("Adresse email invalide.")

        password = os.getenv('COMPTE_PASSWORD') or getpass.getpass(
            f"Mot de passe pour {email} (saisie masquée) : "
        )
        try:
            validate_password(password)
        except ValidationError as erreur:
            raise CommandError(' '.join(erreur.messages))

        role = options['role']
        modele = get_user_model()
        user = modele.objects.filter(email__iexact=email).first()
        cree = user is None
        if cree:
            user = modele(username=email)
        user.email = email
        user.first_name = options['prenom'] or user.first_name
        user.last_name = options['nom'] or user.last_name
        user.is_active = True
        user.is_superuser = user.is_staff = role == SUPER_ADMIN_GROUP
        user.set_password(password)
        user.save()
        user.groups.set([Group.objects.get_or_create(name=role)[0]])
        self.stdout.write(self.style.SUCCESS(
            f"Compte {email} {'créé' if cree else 'mis à jour'} avec le profil {role}."
        ))
