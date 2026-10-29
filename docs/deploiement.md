# Déploiement de MaSalle

Ce document décrit comment déployer MaSalle (Docker, cluster Kubernetes, GitLab CI).
Les points marqués « testé » ont été vérifiés avec Docker Compose ; les exemples
Kubernetes et GitLab sont à adapter à votre cluster.

## 1. Architecture

| Élément | Image | Port | Rôle |
|---|---|---|---|
| `backend` | `backend/Dockerfile` (Python 3.13, gunicorn) | 8000 | API Django, fichiers statiques (WhiteNoise), photos de profil |
| `web` | `Uniserv/Dockerfile` (nginx **sans privilèges**) | 8080 | Site React ; relaie `/api`, `/admin`, `/static`, `/media` vers `backend` |
| PostgreSQL 17 | officielle | 5432 | Base de données (externe ou dans le cluster) |

Le site et l'API partagent la même adresse : pas de CORS à gérer en production
(`VITE_API_URL=/api` est fixé à la construction du site).

## 2. Essai rapide avec Docker Compose (testé)

```powershell
copy .env.docker.example .env      # puis renseigner POSTGRES_PASSWORD et DJANGO_SECRET_KEY
docker compose up -d --build
docker compose exec backend python manage.py creer_compte --email prenom.nom@exemple.com --role SUPER_ADMIN
```

Le site est alors sur <http://localhost:8088> (changez `WEB_PORT` dans `.env`).
Arrêt : `docker compose down` (les données restent) ou `docker compose down -v` (tout effacer).

## 3. Variables d'environnement du backend

| Variable | Obligatoire | Rôle |
|---|---|---|
| `DJANGO_SECRET_KEY` | **oui** | Clé secrète (l'application refuse de démarrer sans elle). À stocker dans un Secret. |
| `DJANGO_DEBUG` | non (`False`) | Ne jamais activer en production. |
| `DJANGO_ALLOWED_HOSTS` | **oui** | Noms de domaine du site, séparés par des virgules. |
| `CSRF_TRUSTED_ORIGINS` | oui | Adresses complètes du site, ex. `https://masalle.exemple.com`. |
| `CORS_ALLOWED_ORIGINS` | non | Utile seulement si le site et l'API sont sur des adresses différentes. |
| `FRONTEND_URL` | oui | Adresse du site, utilisée dans les emails. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | oui | Base de données. Mot de passe dans un Secret. |
| `DJANGO_BEHIND_PROXY` | oui derrière HTTPS | `True` si un ingress / proxy HTTPS termine TLS et envoie `X-Forwarded-Proto`. |
| `API_NUM_PROXIES` | **oui derrière un proxy** | Nombre de proxys de confiance devant l'application (nginx seul : `1` ; ingress + nginx : `2`). Voir §6. |
| `DJANGO_SERVE_MEDIA` | si photos | `True` : l'application sert les photos de profil. |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | pour les emails | SMTP réel (sinon les emails sont seulement affichés dans les journaux). |
| `RUN_MIGRATIONS` | non | `1` : applique les migrations au démarrage (Docker Compose seulement, voir §4). |

Par défaut, HTTPS est exigé (`DJANGO_SECURE_SSL_REDIRECT`, HSTS, cookies sécurisés).
Pour un essai en HTTP, désactivez-les comme dans `.env.docker.example`.

## 4. Migrations

- `python manage.py migrate --noinput` sur une base **vide** crée tout : tables, index,
  les trois profils (`SUPER_ADMIN`, `RH`, `MANAGER`) et les trois salles du siège.
  C'est idempotent (une seconde exécution ne change rien) — testé.
- Sur Kubernetes, lancez-le dans un **Job** avant (ou en pre-install hook de Helm), et
  **pas** au démarrage de chaque pod : plusieurs réplicas ne doivent pas migrer en même temps.
- Aucun compte n'est créé par les migrations (aucun mot de passe dans le code) : le premier
  administrateur se crée avec la commande ci-dessous.

```bash
kubectl exec -it deploy/masalle-backend -- \
  python manage.py creer_compte --email prenom.nom@exemple.com --role SUPER_ADMIN
```

Le mot de passe est saisi de façon masquée (ou fourni par la variable `COMPTE_PASSWORD`).
Le Super Admin crée ensuite les comptes RH et Manager depuis l'application.

## 5. Kubernetes : points d'attention

**Sondes** (sans authentification, indépendantes de l'en-tête `Host` et de la redirection HTTPS) :

```yaml
livenessProbe:   { httpGet: { path: /api/health/, port: 8000 }, periodSeconds: 10 }
readinessProbe:  { httpGet: { path: /api/ready/,  port: 8000 }, periodSeconds: 10 }   # vérifie aussi la base
```

**Rappels 2 heures avant les réunions** : un CronJob chaque minute.

```yaml
schedule: "* * * * *"
concurrencyPolicy: Forbid
command: ["python", "manage.py", "envoyer_rappels"]
```

**Photos de profil** : elles sont enregistrées dans `/app/media`. Montez un volume
persistant dessus (`ReadWriteMany` si plusieurs réplicas du backend). Sans volume,
elles disparaissent à chaque redémarrage de pod.

**Sécurité des pods** : les deux images fonctionnent sans droits root (backend : utilisateur
`1000`, web : nginx sans privilèges) et sont compatibles avec `runAsNonRoot` et
`allowPrivilegeEscalation: false`. Le système de fichiers du backend n'a besoin d'écriture
que sur `/app/media` (et `/tmp`).

**Ingress** : deux façons de router.
1. Tout vers le service `web` (port 8080) : il relaie lui-même `/api`, `/admin`, `/static`, `/media`.
2. `/api`, `/admin`, `/static`, `/media` vers `backend:8000`, et `/` vers `web:8080`.

Dans les deux cas, l'ingress doit conserver l'en-tête `Host` d'origine (avec le port s'il y en a un)
et ajouter `X-Forwarded-For` / `X-Forwarded-Proto`.

**Stockage des fichiers statiques** : ils sont construits dans l'image du backend et servis par
l'application (WhiteNoise) : aucun volume partagé n'est nécessaire.

## 6. Limitation de requêtes derrière un proxy (important)

La limite de tentatives de connexion et le débit de l'API sont calculés par adresse. Derrière un
ingress, l'adresse de connexion est celle du proxy : sans réglage, **tous les utilisateurs partagent
la même limite**. Définissez `API_NUM_PROXIES` au nombre exact de proxys de confiance. Valeur par
défaut `0` : l'en-tête `X-Forwarded-For` est ignoré, donc il ne peut pas être falsifié pour contourner
la limite (testé).

## 7. Sécurité : synthèse de l'audit

- `manage.py check --deploy` : aucun avertissement.
- Dépendances : `pip-audit` et `npm audit` : aucune vulnérabilité connue (au moment de l'audit).
- Analyse du code (Bandit) : aucune alerte de gravité moyenne ou haute.
- Aucun secret dans le dépôt : `.env` est ignoré, les mots de passe se saisissent par commande.
- Connexion : email + mot de passe, message d'erreur unique, limite par adresse et par compte,
  jeton par appareil avec expiration et déconnexion côté serveur, sessions coupées lors d'un
  changement de rôle, de mot de passe ou d'une désactivation.
- Vue écran publique : aucune donnée personnelle, objet remplacé par « Réunion ».

À prévoir côté infrastructure : HTTPS (certificat), sauvegardes de PostgreSQL, serveur SMTP,
et un utilisateur PostgreSQL dédié à l'application.

## 8. GitLab CI (exemple à adapter, non exécuté)

```yaml
stages: [test, build]

backend-tests:
  stage: test
  image: python:3.13-slim
  services: [{ name: "postgres:17", alias: db }]
  variables:
    POSTGRES_DB: gestion_salles
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_HOST: db
    DJANGO_DEBUG: "True"
  script:
    - cd backend && pip install -r requirements.txt
    - python manage.py check
    - python manage.py makemigrations --check --dry-run
    - python manage.py test

frontend:
  stage: test
  image: node:22-alpine
  script:
    - cd Uniserv && npm ci && npm audit --audit-level=high && npm run lint && npm run build
  variables: { VITE_API_URL: /api }

images:
  stage: build
  image: docker:27
  services: [docker:27-dind]
  rules: [{ if: '$CI_COMMIT_BRANCH == "main"' }]
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker build -t "$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHORT_SHA" backend
    - docker build -t "$CI_REGISTRY_IMAGE/web:$CI_COMMIT_SHORT_SHA" Uniserv
    - docker push "$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHORT_SHA"
    - docker push "$CI_REGISTRY_IMAGE/web:$CI_COMMIT_SHORT_SHA"
```

**SonarQube** : analysez `backend/reservations`, `backend/config` et `Uniserv/src`, en excluant
`**/migrations/**`, `**/tests.py`, `**/node_modules/**` et `**/dist/**`. Pour une couverture de tests,
générez un rapport avec `coverage` (non inclus dans les dépendances de production).
