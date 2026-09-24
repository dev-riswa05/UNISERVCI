# Gestion des salles de réunion — UNISERV BTP

Interface React utilisée par le service RH pour consulter le planning et gérer
les réservations de salles.

## Démarrage local

Prérequis : Node.js, le backend Django et MySQL/WampServer démarrés.

```powershell
cd C:\Users\Hp\Desktop\Uniservci\Uniserv
npm install
npm run dev
```

L'interface est ensuite accessible sur <http://localhost:5173>.

## Test depuis le même réseau Wi-Fi

L'adresse Wi-Fi actuelle de cet ordinateur est `10.0.0.99`.

Lancer Django en écoutant sur le réseau :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

Dans un second terminal, lancer le frontend :

```powershell
cd C:\Users\Hp\Desktop\Uniservci\Uniserv
npm run dev
```

Les autres personnes connectées au même réseau peuvent ensuite ouvrir :

<http://10.0.0.99:5173>

Si l'adresse IP de l'ordinateur change, remplacer `10.0.0.99` dans
`backend/.env`. Il peut aussi être nécessaire d'autoriser les ports `5173` et
`8000` dans le pare-feu Windows lors de la première connexion.

## Architecture importante

- `src/lib/api.js` centralise l'URL de Django, le token et les erreurs HTTP.
- `src/components/ProtectedRoute.jsx` protège les routes React.
- `src/pages/ReservationForm.jsx` sert à la création et à la modification.
- Django reste responsable de la sécurité, des conflits et de l'identité du RH.

## Variables d'environnement

Copier `.env.example` vers `.env` seulement si l'URL de l'API doit changer.
Les variables commençant par `VITE_` sont intégrées au build frontend et ne
doivent donc jamais contenir de mot de passe ou de secret.

## Vérifications

```powershell
npm run lint
npm run build
```
