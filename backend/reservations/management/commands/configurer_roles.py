import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from reservations.permissions import DISPLAY_GROUP, RH_GROUP, SUPER_ADMIN_GROUP


class Command(BaseCommand):
    help = "Crée les groupes applicatifs et configure le Super Admin de développement."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='WARIS')
        parser.add_argument('--email', default='waris@uniservci.net')
        parser.add_argument('--password', default=None)

    def handle(self, *args, **options):
        for name in (SUPER_ADMIN_GROUP, RH_GROUP, DISPLAY_GROUP):
            Group.objects.get_or_create(name=name)
        password = options['password'] or os.getenv('SUPER_ADMIN_PASSWORD')
        if not password:
            raise CommandError('Utilisez --password ou SUPER_ADMIN_PASSWORD.')
        model = get_user_model()
        user, _ = model.objects.get_or_create(username=options['username'])
        user.username = options['username']; user.email = options['email']; user.is_active = True
        user.is_staff = True; user.is_superuser = True
        user.set_password(password); user.save()
        user.groups.clear(); user.groups.add(Group.objects.get(name=SUPER_ADMIN_GROUP))
        self.stdout.write(self.style.SUCCESS(f'Super Admin {user.username} configuré.'))
