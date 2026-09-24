import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from reservations.permissions import DISPLAY_GROUP


class Command(BaseCommand):
    help = "Crée ou met à jour le compte technique des tablettes."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='affichage_salles')
        parser.add_argument('--password', default=None)

    def handle(self, *args, **options):
        username = options['username']
        password = options['password'] or os.getenv('AFFICHAGE_PASSWORD')

        if not password:
            password = getpass.getpass(
                f"Mot de passe pour {username} (saisie masquée) : "
            )
        if len(password) < 12:
            raise CommandError(
                "Le mot de passe technique doit contenir au moins 12 caractères."
            )

        user_model = get_user_model()
        group, _ = Group.objects.get_or_create(name=DISPLAY_GROUP)
        user, created = user_model.objects.get_or_create(username=username)

        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()
        user.groups.clear()
        user.groups.add(group)
        Token.objects.get_or_create(user=user)

        action = "créé" if created else "mis à jour"
        self.stdout.write(
            self.style.SUCCESS(
                f"Compte {username} {action} avec le profil {DISPLAY_GROUP}."
            )
        )
        self.stdout.write(
            "Le token reste stocké dans Django et n'est jamais affiché ni codé dans React."
        )
