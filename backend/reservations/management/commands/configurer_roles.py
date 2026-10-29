from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from reservations.permissions import MANAGER_GROUP, RH_GROUP, SUPER_ADMIN_GROUP


class Command(BaseCommand):
    help = (
        "Crée les groupes applicatifs (Super Admin, RH, Manager). "
        "Pour créer un compte, utilisez : python manage.py creer_compte --email ... --role ..."
    )

    def handle(self, *args, **options):
        for name in (SUPER_ADMIN_GROUP, RH_GROUP, MANAGER_GROUP):
            _, cree = Group.objects.get_or_create(name=name)
            self.stdout.write(f"Groupe {name} : {'créé' if cree else 'déjà présent'}.")
