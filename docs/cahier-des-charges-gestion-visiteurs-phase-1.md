# Cahier des charges - Gestion des visiteurs - Phase 1

**Projet :** UNISERV CI - Application d'accueil et de tracabilite des visiteurs  
**Version :** 1.0  
**Date de cadrage :** 24 septembre 2026  
**Echeance maximale de la phase 1 :** 27 septembre 2026  
**Duree :** 3 jours calendaires (J1 a J3)

## 1. Contexte

L'entreprise souhaite remplacer le suivi manuel des visiteurs par une application web simple, rapide et utilisable sur une tablette a l'accueil. La RH ou l'agente d'accueil enregistre les informations du visiteur, valide son entree, visualise les personnes encore presentes et enregistre leur sortie.

Le projet existant contient deja une base React/Tailwind et Django REST Framework/MySQL, mais son domaine fonctionnel actuel est la reservation de salles. La phase 1 doit donc reutiliser le socle technique sans conserver les regles metier de reservation pour le parcours visiteurs.

## 2. Objectifs

- connaitre en temps reel les visiteurs presents dans les locaux ;
- conserver un historique fiable des entrees et sorties ;
- horodater l'entree et la sortie exclusivement cote serveur ;
- permettre une saisie en moins de deux minutes sur tablette ;
- proteger les donnees d'identite et limiter leur acces aux personnes autorisees ;
- garantir qu'un meme livrable fonctionne en developpement sous Windows et en production sous Linux.

## 3. Utilisateurs et droits

### Agente d'accueil / RH

- se connecter a l'application ;
- enregistrer un visiteur et son entree ;
- prendre ou joindre une photo facultative ;
- consulter les visiteurs presents ;
- enregistrer une sortie ;
- consulter et filtrer l'historique.

### Administrateur

- disposer de tous les droits RH ;
- gerer les comptes autorises ;
- consulter les journaux techniques et appliquer la politique de conservation ;
- exporter l'historique si cette option est retenue.

Les visiteurs n'ont aucun compte et aucun acces direct a l'application en phase 1.

## 4. Perimetre fonctionnel

### 4.1 Authentification

- connexion par identifiant et mot de passe ;
- session limitee dans le temps ;
- deconnexion explicite ;
- refus de toutes les routes metier aux utilisateurs non authentifies.

### 4.2 Enregistrement d'une entree

Champs obligatoires :

- nom ;
- prenom ;
- type de piece d'identite ;
- numero de piece d'identite ;
- numero de telephone ;
- personne visitee ou service visite.

Champs facultatifs :

- entreprise ou organisation ;
- motif de la visite ;
- photo du visiteur.

Au clic sur **Enregistrer l'entree**, le serveur enregistre automatiquement la date et l'heure selon le fuseau `Africa/Abidjan` et affecte le statut `PRESENT`. L'heure ne peut pas etre saisie ou modifiee depuis la tablette.

### 4.3 Liste des presents

- affichage des visites dont la sortie n'est pas encore enregistree ;
- recherche par nom, telephone, entreprise, personne ou service visite ;
- affichage immediat du nom, de la destination, de l'heure d'entree et de la photo lorsqu'elle existe ;
- action de sortie accessible en un clic, suivie d'une confirmation courte pour eviter une erreur tactile.

### 4.4 Enregistrement d'une sortie

Au clic sur **Enregistrer la sortie**, le serveur renseigne automatiquement l'heure de sortie et affecte le statut `SORTI`. Une seconde sortie est refusee par l'API et ne modifie pas le premier horodatage.

### 4.5 Historique

- liste paginee des visites terminees et en cours ;
- filtres par periode, statut, visiteur, entreprise et personne/service visite ;
- tri du plus recent au plus ancien ;
- consultation du detail d'une visite ;
- aucune suppression directe par un utilisateur standard.

### 4.6 Hors perimetre de la phase 1

- badge physique, QR code ou impression d'etiquette ;
- notification automatique de la personne visitee ;
- pre-enregistrement par le visiteur ;
- signature electronique ;
- lecture automatique de CNI ;
- mode hors connexion complet et synchronisation differee ;
- statistiques avancees et integration a un annuaire d'entreprise.

## 5. Regles de gestion

- `date_heure_entree` est genere par Django lors de la validation de l'entree.
- `date_heure_sortie` est nul tant que le visiteur est present, puis genere par Django lors de la sortie.
- Une visite est `PRESENT` si la sortie est nulle et `SORTI` dans le cas contraire.
- Une sortie ne peut pas preceder l'entree.
- Le numero de piece doit etre chiffre en base ou, au minimum, masque dans toutes les listes et les journaux.
- La photo est facultative, limitee aux formats JPEG/PNG/WebP et a une taille definie (recommandation : 5 Mo maximum).
- Les dates sont stockees en UTC et affichees dans le fuseau `Africa/Abidjan`.
- Chaque creation et sortie conserve l'utilisateur responsable et l'horodatage de l'action.
- La duree de conservation des pieces, numeros et photos doit etre validee par la direction avant la mise en production.

## 6. Modele de donnees minimal

### Visiteur

- `id`
- `nom`, `prenom`
- `type_piece`, `numero_piece_chiffre`
- `telephone`
- `entreprise` (facultatif)
- `photo` (facultative)
- `created_at`, `updated_at`

### Visite

- `id`
- `visiteur_id`
- `personne_ou_service_visite`
- `motif` (facultatif)
- `date_heure_entree`
- `date_heure_sortie` (facultative)
- `cree_par`, `sortie_enregistree_par`
- `created_at`, `updated_at`

Les comptes applicatifs restent portes par le systeme d'authentification Django. La separation `Visiteur` / `Visite` evite de ressaisir une personne recurrente tout en conservant un historique distinct pour chaque passage.

## 7. API minimale

- `POST /api/auth/login/` : connexion ;
- `POST /api/auth/logout/` : deconnexion ;
- `GET /api/visites/presents/` : visiteurs actuellement presents ;
- `POST /api/visites/` : creation d'un visiteur et de son entree ;
- `POST /api/visites/{id}/sortie/` : enregistrement atomique de la sortie ;
- `GET /api/visites/` : historique filtre et pagine ;
- `GET /api/visites/{id}/` : detail d'une visite.

Les validations, droits et horodatages doivent etre appliques dans l'API, meme si l'interface effectue aussi des controles ergonomiques.

## 8. Exigences d'interface tablette

- affichage cible a partir de 768 px de large, utilisable aussi sur ordinateur ;
- zones tactiles d'au moins 44 x 44 px ;
- formulaire sur une seule colonne en mode portrait ;
- boutons d'entree et de sortie clairement differencies ;
- messages de validation proches des champs concernes ;
- indicateur visible du nombre de visiteurs presents ;
- prise de photo via le navigateur avec repli vers la selection d'un fichier ;
- temps de reponse percu inferieur a deux secondes sur le reseau interne dans les conditions normales.

## 9. Stack technique retenue

### Developpement Windows

- Windows 10/11 ;
- Git ;
- Python 3.14 avec environnement virtuel `.venv` ;
- Django 6.0.7 et Django REST Framework 3.17.1 ;
- Node.js 24 et npm 11 ;
- React 19, Vite 8 et Tailwind CSS 4 ;
- MySQL 8.x local (WampServer acceptable en developpement uniquement).

### Production Linux

- images Docker Linux reproductibles, construites sans reprendre `node_modules` ni `.venv` de Windows ;
- frontend compile par Node puis servi en fichiers statiques par Nginx ;
- API Django executee par Gunicorn derriere Nginx ou l'Ingress du cluster ;
- MySQL 8.x persistant, de preference service manage ou instance distincte du pod applicatif ;
- stockage persistant objet ou volume partage pour les photos ;
- secrets injectes par variables d'environnement ou gestionnaire de secrets ;
- phpMyAdmin facultatif, reserve a l'IT, non expose publiquement et protege par le reseau/VPN.

### Compatibilite Windows/Linux

- utiliser `pathlib` pour tous les chemins ;
- utiliser des noms de fichiers en minuscules et respecter la casse des imports ;
- conserver les fins de ligne et scripts compatibles via Git ;
- ne jamais coder de chemin `C:\\...` dans l'application ;
- installer les dependances dans chaque OS a partir des fichiers verrouilles ;
- construire et tester l'image Linux avant chaque livraison ;
- stocker les dates en UTC et configurer explicitement le fuseau d'affichage ;
- ne pas utiliser le serveur `runserver` ou `vite dev` en production.

## 10. Architecture cible

```text
Tablette / navigateur HTTPS
          |
     Nginx / Ingress
       /        \
React statique   API Django + Gunicorn
                       |
                    MySQL 8
                       |
             Volume/stockage des photos
```

Dans un cluster, l'API doit rester sans etat local. Les sessions, donnees et photos ne doivent pas dependre du disque temporaire d'un conteneur.

## 11. Securite et confidentialite

- HTTPS obligatoire en production ;
- mots de passe geres par Django, jamais stockes en clair ;
- controle d'acces par role sur chaque endpoint ;
- limitation des tentatives de connexion ;
- aucun numero de piece, token ou mot de passe dans les logs ;
- sauvegarde chiffree de MySQL et test de restauration ;
- politique documentee de conservation et de purge des donnees ;
- consentement/information du visiteur a valider pour la photo et les donnees d'identite ;
- journalisation des entrees, sorties et actions administratives ;
- acces phpMyAdmin limite au reseau d'administration.

## 12. Plan de realisation sur 3 jours

### J1 - 25 septembre 2026 : socle et entree

- creer le domaine `visiteurs` sans casser le code existant ;
- creer les modeles, migrations et regles de validation ;
- implementer authentification, creation d'entree et upload photo ;
- creer l'ecran tablette de saisie ;
- ajouter les tests API de creation et de permissions.

**Livrable J1 :** une RH connectee peut enregistrer une entree horodatee automatiquement.

### J2 - 26 septembre 2026 : presence, sortie et historique

- implementer la liste des presents et la recherche ;
- implementer la sortie atomique et son controle de double clic ;
- implementer l'historique filtre et pagine ;
- finaliser les ecrans tablette et les etats d'erreur/chargement ;
- ajouter les tests du parcours complet entree-sortie.

**Livrable J2 :** le parcours fonctionnel complet est testable depuis la tablette.

### J3 - 27 septembre 2026 : Linux, recette et livraison

- ajouter les Dockerfiles, la configuration Gunicorn/Nginx et l'orchestration cible ;
- configurer les variables, volumes, migrations, health checks et donnees statiques ;
- executer lint, build, tests backend et test de l'image Linux ;
- realiser la recette sur tablette ;
- corriger les anomalies bloquantes et livrer la procedure d'exploitation.

**Livrable J3 :** phase 1 validee, image Linux reproductible et dossier de deploiement pret.

Le delai de trois jours correspond a un MVP strict. Toute fonctionnalite hors perimetre ou toute migration complexe de donnees doit etre planifiee apres cette echeance.

## 13. Criteres de recette

La phase 1 est acceptee lorsque :

- une RH authentifiee enregistre tous les champs obligatoires depuis une tablette ;
- l'API refuse une entree incomplete ;
- l'heure d'entree correspond a l'heure du serveur et n'est pas fournie par le client ;
- le visiteur apparait immediatement dans la liste des presents ;
- une sortie renseigne l'heure serveur, retire le visiteur des presents et conserve la visite dans l'historique ;
- une seconde sortie est refusee sans alterer les donnees ;
- les recherches et filtres principaux fonctionnent ;
- un utilisateur non authentifie ne peut consulter aucune donnee visiteur ;
- la photo facultative fonctionne et une visite sans photo reste valide ;
- les tests automatises, le lint et le build sont verts ;
- l'image est construite et demarree sous Linux avec MySQL ;
- l'interface ne presente ni debordement ni chevauchement en portrait et paysage sur la tablette cible ;
- une sauvegarde et une restauration MySQL ont ete testees.

## 14. Audit de l'environnement actuel

### Deja disponible et fonctionnel

- Git 2.51.0 ;
- Python 3.14.0 ;
- environnement virtuel backend existant ;
- Django 6.0.7, DRF 3.17.1, `django-cors-headers` 4.9.0 et `mysqlclient` 2.2.8 ;
- `python manage.py check` sans erreur ;
- Node.js 24.8.0 et npm 11.6.0 ;
- React, Vite, Tailwind et routage deja installes ;
- configuration `.env` separee pour le frontend et le backend ;
- fuseau Django deja configure sur `Africa/Abidjan` ;
- premiers reglages HTTPS, CORS, cookies et limitation de connexion deja presents.

### A installer ou ajouter

- Docker Desktop avec WSL2 pour construire et tester localement les images Linux ;
- MySQL 8.x accessible au projet ou confirmation du service MySQL de WampServer ;
- Gunicorn dans les dependances de production ;
- Pillow pour traiter les champs image cote Django ;
- Nginx ou une configuration Ingress ;
- Dockerfiles frontend/backend et fichier d'orchestration ;
- `.dockerignore` pour exclure `.venv`, `node_modules`, logs, `.env` et bases locales ;
- configuration de `STATIC_ROOT`, collecte des fichiers statiques et stockage persistant des medias ;
- health checks, journalisation vers stdout et procedure de migrations ;
- tests automatises du nouveau domaine visiteurs ;
- fichier de dependances ou image verrouillant aussi les paquets systeme Linux necessaires a `mysqlclient`.

### Points a corriger avant la production

- le projet actuel gere les salles et reservations, pas encore les visiteurs ;
- le nom de base par defaut est encore `gestion_salles` ;
- `db.sqlite3` coexiste dans le depot alors que la configuration active vise MySQL ;
- les fichiers `.venv` Windows et `node_modules` ne doivent jamais etre copies dans une image Linux ;
- le serveur Django de developpement et Vite ne conviennent pas a la production ;
- les photos sont actuellement prevues sur un dossier media local, ce qui n'est pas partage entre plusieurs noeuds ;
- l'envoi asynchrone par thread du projet de reservation n'est pas adapte a une architecture multi-conteneurs ;
- aucun Dockerfile, manifeste de cluster, proxy de production ou health check n'est present ;
- certains fichiers affichent des caracteres francais mal encodes et doivent etre normalises en UTF-8 ;
- les versions installees dans `node_modules` divergent legerement de celles declarees, donc `npm ci` doit devenir la reference de construction.

## 15. Livrables

- code source frontend et backend ;
- migrations Django ;
- tests automatises ;
- fichiers de construction et de deploiement Linux ;
- exemples de variables d'environnement sans secrets ;
- guide d'installation Windows ;
- guide de deploiement et d'exploitation Linux ;
- fiche de recette signee ;
- politique de sauvegarde, restauration et conservation des donnees.

## 16. Risques et decisions attendues

- **Cluster exact non precise :** confirmer Kubernetes, Docker Swarm ou autre orchestrateur avant d'ecrire les manifestes definitifs.
- **Donnees sensibles :** valider la base legale, la duree de conservation et le droit de prendre une photo.
- **Camera tablette :** tester des J1 sur le navigateur et le modele de tablette reels ; HTTPS est generalement requis pour l'acces camera en production.
- **Disponibilite en trois jours :** maintenir strictement le perimetre MVP et reporter les integrations secondaires.
- **MySQL :** confirmer l'hebergement, les sauvegardes et les identifiants de production avant J3.

