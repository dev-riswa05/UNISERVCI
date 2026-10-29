# Gestion des salles de réunion — UNISERV BTP

Application interne composée d'un frontend React/Tailwind et d'une API
Django REST Framework connectée à MySQL.

## Démarrer le projet

1. Démarrer WampServer et vérifier que MySQL écoute sur le port `3306`.
2. Lancer Django :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

3. Dans un second terminal, lancer React :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\Uniserv
npm run dev
```

4. Ouvrir <http://localhost:5173>. La page d'accueil propose deux boutons :
   **Se connecter** (email + mot de passe, la redirection se fait selon le profil)
   et **Écran** (vue publique de toutes les salles, sans connexion).

## Parcours d'une réservation

1. React demande les salles libres pour la date et les heures choisies.
2. Django recalcule toujours les conflits avant l'enregistrement.
3. Django associe automatiquement la réservation au RH connecté.
4. La réservation, les participants et le rappel H-2 sont enregistrés.
5. Les e-mails sont déclenchés après validation de la transaction MySQL.
6. Une annulation conserve l'historique et annule aussi le rappel.

## Configuration

Les exemples se trouvent dans `backend/.env.example` et
`Uniserv/.env.example`. Les valeurs actuelles restent compatibles avec le
développement local sans fichier `.env`.

Avant la production, définir au minimum une nouvelle `DJANGO_SECRET_KEY`,
passer `DJANGO_DEBUG=False`, renseigner `DJANGO_ALLOWED_HOSTS` et configurer le
backend SMTP.

## Docker et déploiement

```powershell
copy .env.docker.example .env      # renseigner POSTGRES_PASSWORD et DJANGO_SECRET_KEY
docker compose up -d --build       # site sur http://localhost:8088
```

Le guide complet (variables, migrations, sondes Kubernetes, rappels, GitLab CI, synthèse de
l'audit de sécurité) est dans [docs/deploiement.md](docs/deploiement.md).

## Tests automatiques

```powershell
cd C:\Users\Hp\Desktop\Uniservci\backend
python manage.py test                                   # base configurée dans .env (PostgreSQL)
python manage.py test --settings=config.settings_test  # SQLite en mémoire, sans serveur
```

## Profils et comptes

| Profil | Accès |
|---|---|
| **Super Admin** | Tout, y compris les salles et les comptes (page Administration) |
| **RH** | Toutes les réservations, le planning, le tableau de bord, l'export |
| **Manager** | Crée des réservations, modifie ou annule les siennes. Voit l'occupation de toutes les salles, mais le détail seulement de ses propres réservations. |

La connexion se fait par **adresse email** (insensible à la casse) et mot de
passe. Le profil est lu côté serveur : l'utilisateur n'a pas à le choisir.
L'historique « créée par / modifiée par / annulée par » est rattaché à la
personne (nom complet, sinon email).

Créer ou mettre à jour un compte en ligne de commande (mot de passe saisi de
façon masquée, ou variable `COMPTE_PASSWORD`) :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\backend
python manage.py configurer_roles
python manage.py creer_compte --email prenom.nom@exemple.com --role SUPER_ADMIN
```

Les rôles possibles sont `SUPER_ADMIN`, `RH` et `MANAGER`. Une fois connecté, le
Super Admin crée les comptes RH et Manager depuis la page Administration.

## Vue écran publique

`/affichage` est publique, en lecture seule, et affiche toutes les salles du
jour (salle, horaire, libre ou occupé). Elle n'expose ni nom, ni email, ni note,
et l'objet des réunions est remplacé par « Réunion ». Le nombre de requêtes par
adresse est limité (`API_AFFICHAGE_RATE`).

## Checklist avant mise en production

- utiliser `DJANGO_DEBUG=False` et une nouvelle `DJANGO_SECRET_KEY` ;
- configurer HTTPS, `DJANGO_ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS` ;
- renseigner le serveur SMTP et lancer `envoyer_rappels` toutes les minutes ;
- sauvegarder quotidiennement MySQL et tester régulièrement la restauration ;
- régler `RH_SESSION_MAX_AGE` et `API_LOGIN_RATE` selon la politique interne ;
- exécuter `python manage.py check`, `python manage.py test`,
  `npm run lint` et `npm run build` avant chaque déploiement.

L'administration fonctionnelle est disponible dans `/administration`
(Super Admin uniquement).
