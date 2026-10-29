from django.db import connection
from django.http import JsonResponse

LIVE = '/api/health/'
READY = '/api/ready/'


class HealthCheckMiddleware:
    """Contrôles de santé pour Kubernetes (liveness / readiness).

    Placé tout en haut de la pile : la réponse ne dépend ni de l'en-tête Host
    (les sondes du cluster appellent l'adresse IP du pod), ni de la redirection
    HTTPS, ni de l'authentification, ni de la limitation de requêtes.

    - /api/health/ : l'application répond (ne touche pas à la base).
    - /api/ready/  : l'application ET la base de données répondent.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == LIVE:
            return JsonResponse({'status': 'ok'})
        if request.path == READY:
            try:
                connection.ensure_connection()
            except Exception:
                return JsonResponse({'status': 'base indisponible'}, status=503)
            return JsonResponse({'status': 'ok'})
        return self.get_response(request)
