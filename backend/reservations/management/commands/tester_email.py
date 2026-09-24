from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Envoie un email de diagnostic via le backend email configuré."

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='Adresse destinataire de test')

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND.endswith('smtp.EmailBackend'):
            missing = [name for name in ('EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD') if not getattr(settings, name, '')]
            if missing:
                raise CommandError('Configuration SMTP incomplète : ' + ', '.join(missing))
        try:
            sent = send_mail(
                subject='Test SMTP — UNISERV BTP',
                message="Email de diagnostic de l'application de gestion des salles UNISERV BTP.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[options['to']],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Échec SMTP : {exc}') from exc
        if sent != 1:
            raise CommandError("Le backend email n'a confirmé aucun envoi.")
        self.stdout.write(self.style.SUCCESS(f'Email de test accepté par {settings.EMAIL_BACKEND}.'))
