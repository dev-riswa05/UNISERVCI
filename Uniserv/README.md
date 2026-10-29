# Gestion des salles de réunion — UNISERV BTP

Interface React utilisée par le service RH pour consulter le planning et gérer
les réservations de salles.

## Démarrage local

Prérequis : Node.js, le backend Django et MySQL/WampServer démarrés.

```powershell
cd <chemin-du-projet>/Uniserv
npm install
npm run dev
```

L'interface est ensuite accessible sur <http://localhost:5173>.

## Architecture importante

- `src/lib/api.js` centralise l'URL de Django, le token et les erreurs HTTP.
- `src/components/ProtectedRoute.jsx` protège les routes React.
- `src/pages/ReservationForm.jsx` sert à la création et à la modification.
- Django reste responsable de la sécurité, des conflits et de l'identité du RH.

## Variables d'environnement

Copier `.env.example` vers `.env` seulement si l'URL de l'API doit changer.
Les variables commençant par `VITE_` sont intégrées au build frontend et ne
doivent donc jamais contenir de mot de passe ou de secret.

### Production

`VITE_API_URL` est **obligatoire** pour un build de production (par exemple
`https://api.exemple.com/api`). Sans elle, les appels à l'API échouent avec une
erreur de configuration ; le repli automatique sur le port 8000 n'existe qu'en
développement.

## Rôles et écran d'affichage

- **Super Admin** : gestion complète, y compris l'administration des comptes.
- **RH** : gestion des salles et des réservations.
- **Affichage** : compte dédié aux tablettes, limité à la route `/affichage`
  (disponibilités en temps réel, actualisation toutes les minutes, heure de
  Côte d'Ivoire). Un compte Affichage n'accède pas au reste de l'application.

## Vérifications

```powershell
npm run lint
npm run build
```
