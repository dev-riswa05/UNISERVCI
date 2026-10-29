#!/bin/sh
# Point d'entrée du conteneur.
# Les migrations ne s'exécutent ici que si RUN_MIGRATIONS=1 (Docker Compose, un seul
# conteneur). Sur Kubernetes, laissez-le désactivé et lancez `python manage.py migrate`
# dans un Job : plusieurs réplicas ne doivent pas migrer en même temps.
set -e

if [ "$RUN_MIGRATIONS" = "1" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
