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

4. Ouvrir <http://localhost:5173> et se connecter avec le compte RH.

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

## Vérification automatique de la V1

Lorsque WampServer est démarré, cette commande teste les principaux parcours
sans conserver de données techniques dans MySQL :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\backend
python manage.py verifier_v1
```

## Compte technique des tablettes

Créer ou renouveler le compte en saisissant son mot de passe de manière
masquée dans le terminal :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\backend
python manage.py configurer_affichage
```

Le compte `affichage_salles` appartient au groupe Django `AFFICHAGE`. Il peut
uniquement consulter `/api/affichage/`; toutes les opérations RH lui sont
refusées par Django. Après une première connexion sur chaque tablette, son
token reste dans le stockage local du navigateur et la session est persistante.

Les futurs comptes RH doivent être administrateurs Django ou membres du groupe
`RH`. Un compte Django sans l'un de ces deux profils n'obtient aucun accès à
l'application.

## Checklist avant mise en production

- utiliser `DJANGO_DEBUG=False` et une nouvelle `DJANGO_SECRET_KEY` ;
- configurer HTTPS, `DJANGO_ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS` ;
- renseigner le serveur SMTP et lancer `envoyer_rappels` toutes les minutes ;
- sauvegarder quotidiennement MySQL et tester régulièrement la restauration ;
- régler `RH_SESSION_MAX_AGE` et `API_LOGIN_RATE` selon la politique interne ;
- exécuter `python manage.py check`, `python manage.py verifier_v1`,
  `npm run lint` et `npm run build` avant chaque déploiement.

L'administration fonctionnelle est disponible dans `/administration`. Le
compte technique d'affichage reste strictement limité à `/affichage`.
