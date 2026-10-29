FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Les dépendances d'abord : cette couche est réutilisée tant que
# requirements.txt ne change pas (reconstructions rapides).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fichiers statiques construits UNE fois, dans l'image (servis par WhiteNoise) :
# aucun volume partagé n'est nécessaire, y compris sur Kubernetes. La clé ci-dessous
# ne sert qu'à cette commande de construction et n'est pas conservée.
RUN DJANGO_SECRET_KEY=cle-de-construction-uniquement python manage.py collectstatic --noinput

# Utilisateur sans droits (jamais root dans le conteneur). Le dossier des fichiers
# envoyés lui appartient, pour qu'un volume monté dessus soit accessible en écriture.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/media \
    && sed -i 's/\r$//' docker-entrypoint.sh \
    && chmod +x docker-entrypoint.sh \
    && chown -R app:app /app
USER 1000

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
