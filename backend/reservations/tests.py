from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from unittest import skipUnless

from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from .models import JetonAppareil, Reservations, Salles
from .permissions import MANAGER_GROUP, RH_GROUP, SUPER_ADMIN_GROUP
from .views import neutraliser_formule, valeur_booleenne

MOT_DE_PASSE = 'Mot-de-passe-solide-2026'

# Cache en mémoire : les compteurs de limitation ne doivent ni fausser le
# nombre de requêtes SQL mesuré, ni fuir d'un test à l'autre.
CACHE_MEMOIRE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


class SallesDuSiegeTests(TestCase):
    """Les salles du siège sont créées par migration sur toute base neuve."""

    def test_les_trois_salles_existent_et_sont_actives(self):
        noms = set(Salles.objects.filter(active=True).values_list('nom_salle', flat=True))
        self.assertEqual(noms, {
            'Salle de réunion 6e étage', 'Salle de réunion 4e étage', 'BUREAU DU DG',
        })
        for salle in Salles.objects.all():
            self.assertIn('Immeuble TIAMA', salle.localisation)
            self.assertIn('Résidentiel', salle.localisation)

    def test_relancer_la_creation_ne_duplique_rien_et_respecte_les_modifications(self):
        from importlib import import_module
        from django.apps import apps as registre_apps
        migration = import_module('reservations.migrations.0006_salles_du_siege')
        Salles.objects.filter(nom_salle='BUREAU DU DG').update(capacite=4)
        migration.creer_salles(registre_apps, None)
        self.assertEqual(Salles.objects.count(), 3)
        self.assertEqual(Salles.objects.get(nom_salle='BUREAU DU DG').capacite, 4)


class NeutraliserFormuleTests(SimpleTestCase):
    def test_formules_sont_neutralisees(self):
        for valeur in ('=1+1', '+SUM(A1)', '-2', '@cmd', '\tx'):
            self.assertTrue(neutraliser_formule(valeur).startswith("'"))

    def test_texte_normal_inchange(self):
        self.assertEqual(neutraliser_formule('Réunion RH'), 'Réunion RH')
        self.assertEqual(neutraliser_formule(None), '')


class ValeurBooleenneTests(SimpleTestCase):
    def test_booleens_acceptes(self):
        self.assertIs(valeur_booleenne(True, 'actif'), True)
        self.assertIs(valeur_booleenne('false', 'actif'), False)
        self.assertIs(valeur_booleenne('True', 'actif'), True)

    def test_valeur_invalide_refusee(self):
        with self.assertRaises(ValidationError):
            valeur_booleenne('peut-etre', 'actif')
        with self.assertRaises(ValidationError):
            valeur_booleenne(1, 'actif')


def creer_compte(username, groupe, **extra):
    user = get_user_model().objects.create_user(
        username=username, email=f'{username.lower()}@example.com',
        password=MOT_DE_PASSE, **extra,
    )
    user.groups.add(Group.objects.get_or_create(name=groupe)[0])
    return user


@override_settings(CACHES=CACHE_MEMOIRE)
class ReservationsApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rh = creer_compte('rh', RH_GROUP)
        cls.admin = creer_compte('admin', SUPER_ADMIN_GROUP)
        Salles.objects.all().delete()  # salles du siège créées par migration
        cls.salle = Salles.objects.create(nom_salle='Salle A', capacite=10, active=True)
        cls.demain = date.today() + timedelta(days=1)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.rh)

    def donnees(self, **extra):
        base = {
            'id_salle': self.salle.pk, 'nom_demandeur': 'Alice',
            'email_demandeur': 'alice@example.com', 'objet': 'Point',
            'date_reservation': self.demain.isoformat(),
            'heure_debut': '09:00', 'heure_fin': '10:00',
            'nombre_participants': 2,
            'participants': [{'nom': 'Bob', 'email': 'bob@example.com'}],
        }
        base.update(extra)
        return base

    def test_creation_valide(self):
        reponse = self.client.post('/api/reservations/', self.donnees(), format='json')
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(Reservations.objects.get().statut, 'CONFIRMEE')

    def test_conflit_de_creneau_refuse(self):
        self.client.post('/api/reservations/', self.donnees(), format='json')
        reponse = self.client.post(
            '/api/reservations/',
            self.donnees(heure_debut='09:30', heure_fin='10:30'), format='json',
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(Reservations.objects.count(), 1)

    def test_creneaux_contigus_acceptes(self):
        self.client.post('/api/reservations/', self.donnees(), format='json')
        reponse = self.client.post(
            '/api/reservations/',
            self.donnees(heure_debut='10:00', heure_fin='11:00'), format='json',
        )
        self.assertEqual(reponse.status_code, 201, reponse.data)

    def test_reservation_dans_le_passe_refusee(self):
        hier = (date.today() - timedelta(days=1)).isoformat()
        reponse = self.client.post(
            '/api/reservations/', self.donnees(date_reservation=hier), format='json'
        )
        self.assertEqual(reponse.status_code, 400)

    def test_email_invalide_refuse(self):
        reponse = self.client.post(
            '/api/reservations/', self.donnees(email_demandeur='pas-un-email'), format='json'
        )
        self.assertEqual(reponse.status_code, 400)
        reponse = self.client.post(
            '/api/reservations/',
            self.donnees(participants=[{'nom': 'X', 'email': 'nope'}]), format='json',
        )
        self.assertEqual(reponse.status_code, 400)

    def test_nombre_de_participants_et_capacite(self):
        self.assertEqual(self.client.post(
            '/api/reservations/', self.donnees(nombre_participants=0), format='json'
        ).status_code, 400)
        self.assertEqual(self.client.post(
            '/api/reservations/', self.donnees(nombre_participants=11), format='json'
        ).status_code, 400)

    def test_horaires_hors_ouverture_refuses(self):
        reponse = self.client.post(
            '/api/reservations/',
            self.donnees(heure_debut='07:00', heure_fin='08:00'), format='json',
        )
        self.assertEqual(reponse.status_code, 400)

    def test_annulation_puis_seconde_annulation(self):
        rid = self.client.post(
            '/api/reservations/', self.donnees(), format='json'
        ).data['id_reservation']
        self.assertEqual(self.client.post(f'/api/reservations/{rid}/annuler/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/reservations/{rid}/annuler/').status_code, 400)
        # Le créneau annulé est de nouveau réservable.
        self.assertEqual(self.client.post(
            '/api/reservations/', self.donnees(), format='json'
        ).status_code, 201)

    def test_reservation_annulee_non_modifiable(self):
        rid = self.client.post(
            '/api/reservations/', self.donnees(), format='json'
        ).data['id_reservation']
        self.client.post(f'/api/reservations/{rid}/annuler/')
        reponse = self.client.patch(f'/api/reservations/{rid}/', {'notes': 'x'}, format='json')
        self.assertEqual(reponse.status_code, 400)

    def test_liste_simple_puis_paginee(self):
        for heure in ('09:00', '10:00', '11:00'):
            self.client.post('/api/reservations/', self.donnees(
                heure_debut=heure, heure_fin=f'{int(heure[:2]) + 1:02d}:00'), format='json')
        simple = self.client.get('/api/reservations/')
        self.assertIsInstance(simple.data, list)
        self.assertEqual(len(simple.data), 3)
        paginee = self.client.get('/api/reservations/?page=1&page_size=2')
        self.assertEqual(paginee.data['count'], 3)
        self.assertEqual(len(paginee.data['results']), 2)

    def test_nombre_de_requetes_independant_du_nombre_de_reservations(self):
        def creer(heures):
            for heure in heures:
                self.client.post('/api/reservations/', self.donnees(
                    heure_debut=heure, heure_fin=f'{int(heure[:2]) + 1:02d}:00'), format='json')

        def compter_requetes():
            with CaptureQueriesContext(connection) as contexte:
                self.assertEqual(self.client.get('/api/reservations/').status_code, 200)
            return len(contexte)

        creer(('09:00', '10:00'))
        avec_deux = compter_requetes()
        creer(('11:00', '12:00', '13:00', '14:00'))
        self.assertEqual(compter_requetes(), avec_deux)

    def test_export_csv_neutralise_les_formules(self):
        self.client.post(
            '/api/reservations/', self.donnees(objet='=HYPERLINK("http://x")'), format='json'
        )
        contenu = self.client.get('/api/reservations/export/').content.decode('utf-8')
        self.assertIn("'=HYPERLINK", contenu)

    def test_acces_refuse_sans_connexion(self):
        self.assertEqual(APIClient().get('/api/reservations/').status_code, 401)
        self.assertEqual(APIClient().get('/api/planning/').status_code, 401)

    def test_historique_rattache_a_la_personne(self):
        self.rh.first_name, self.rh.last_name = 'Awa', 'Kone'
        self.rh.save()
        rid = self.client.post(
            '/api/reservations/', self.donnees(), format='json'
        ).data['id_reservation']
        detail = self.client.get(f'/api/reservations/{rid}/').data
        self.assertEqual(detail['created_by_name'], 'Awa Kone')
        self.assertIsNone(detail['updated_by_name'])
        # Sans nom complet, c'est l'email de la personne qui s'affiche.
        self.rh.first_name = self.rh.last_name = ''
        self.rh.save()
        self.client.patch(f'/api/reservations/{rid}/', {'notes': 'maj'}, format='json')
        detail = self.client.get(f'/api/reservations/{rid}/').data
        self.assertEqual(detail['updated_by_name'], 'rh@example.com')


@override_settings(CACHES=CACHE_MEMOIRE)
class EcranPublicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rh = creer_compte('rh', RH_GROUP)
        Salles.objects.all().delete()  # salles du siège créées par migration
        cls.salle_a = Salles.objects.create(nom_salle='Salle A', etage='4e', active=True)
        cls.salle_b = Salles.objects.create(nom_salle='Salle B', etage='6e', active=True)
        Salles.objects.create(nom_salle='Salle fermée', active=False)

    def test_accessible_sans_connexion_et_montre_toutes_les_salles(self):
        reponse = APIClient().get('/api/affichage/')
        self.assertEqual(reponse.status_code, 200)
        noms = {s['nom_salle'] for s in reponse.data['salles']}
        self.assertEqual(noms, {'Salle A', 'Salle B'})

    def test_un_jeton_invalide_ne_bloque_pas_la_page_publique(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token inexistant')
        self.assertEqual(client.get('/api/affichage/').status_code, 200)

    def test_aucune_donnee_personnelle_ni_objet_reel(self):
        demain = date.today() + timedelta(days=1)
        rh = APIClient()
        rh.force_authenticate(self.rh)
        rh.post('/api/reservations/', {
            'id_salle': self.salle_a.pk, 'nom_demandeur': 'Alice Secrete',
            'email_demandeur': 'alice@example.com', 'objet': 'Entretien confidentiel',
            'date_reservation': demain.isoformat(), 'heure_debut': '09:00',
            'heure_fin': '10:00', 'nombre_participants': 1, 'notes': 'note privee',
            'participants': [{'nom': 'Bob', 'email': 'bob@example.com'}],
        }, format='json')
        reponse = APIClient().get(f'/api/affichage/?date={demain.isoformat()}')
        self.assertEqual(len(reponse.data['reservations']), 1)
        self.assertEqual(reponse.data['reservations'][0]['objet'], 'Réunion')
        texte = str(reponse.data)
        for secret in ('Alice', 'Secrete', 'alice@example.com', 'bob@example.com',
                       'Entretien', 'note privee'):
            self.assertNotIn(secret, texte)

    def test_date_invalide_refusee(self):
        self.assertEqual(APIClient().get('/api/affichage/?date=pas-une-date').status_code, 400)


@override_settings(CACHES=CACHE_MEMOIRE)
class ManagerTests(TestCase):
    """Le profil Manager : réserve pour lui-même, sans gérer les autres."""

    @classmethod
    def setUpTestData(cls):
        cls.rh = creer_compte('rh', RH_GROUP)
        cls.manager = creer_compte('mgr', MANAGER_GROUP)
        cls.autre = creer_compte('mgr2', MANAGER_GROUP)
        Salles.objects.all().delete()  # salles du siège créées par migration
        cls.salle = Salles.objects.create(nom_salle='Salle A', capacite=10, active=True)
        cls.demain = (date.today() + timedelta(days=1)).isoformat()

    def client_de(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def reservation(self, **extra):
        base = {
            'id_salle': self.salle.pk, 'nom_demandeur': 'Demandeur',
            'email_demandeur': 'demandeur@example.com', 'objet': 'Sujet prive',
            'date_reservation': self.demain, 'heure_debut': '09:00', 'heure_fin': '10:00',
            'nombre_participants': 1, 'notes': 'note privee',
            'participants': [{'nom': 'Bob', 'email': 'bob@example.com'}],
        }
        base.update(extra)
        return base

    def test_un_manager_cree_puis_gere_sa_reservation(self):
        client = self.client_de(self.manager)
        reponse = client.post('/api/reservations/', self.reservation(), format='json')
        self.assertEqual(reponse.status_code, 201, reponse.data)
        rid = reponse.data['id_reservation']
        self.assertFalse(reponse.data['lecture_seule'])
        self.assertEqual(client.patch(
            f'/api/reservations/{rid}/', {'notes': 'maj'}, format='json').status_code, 200)
        self.assertEqual(client.post(f'/api/reservations/{rid}/annuler/').status_code, 200)

    def test_un_manager_ne_touche_pas_aux_reservations_des_autres(self):
        rid = self.client_de(self.rh).post(
            '/api/reservations/', self.reservation(), format='json'
        ).data['id_reservation']
        for client in (self.client_de(self.manager), self.client_de(self.autre)):
            self.assertEqual(client.get(f'/api/reservations/{rid}/').status_code, 403)
            self.assertEqual(client.patch(
                f'/api/reservations/{rid}/', {'notes': 'x'}, format='json').status_code, 403)
            self.assertEqual(client.post(f'/api/reservations/{rid}/annuler/').status_code, 403)
            self.assertEqual(client.post(
                f'/api/reservations/{rid}/dupliquer/', {}, format='json').status_code, 403)
        self.assertEqual(Reservations.objects.get(pk=rid).statut, 'CONFIRMEE')

    def test_un_manager_voit_les_autres_comme_simple_creneau_occupe(self):
        self.client_de(self.rh).post('/api/reservations/', self.reservation(), format='json')
        self.client_de(self.manager).post(
            '/api/reservations/',
            self.reservation(heure_debut='11:00', heure_fin='12:00', objet='Mon sujet'),
            format='json')
        for url in ('/api/reservations/', f'/api/planning/?date={self.demain}'):
            elements = self.client_de(self.manager).get(url).data
            self.assertEqual(len(elements), 2)
            autres = [e for e in elements if e['lecture_seule']]
            siennes = [e for e in elements if not e['lecture_seule']]
            self.assertEqual(len(autres), 1)
            self.assertEqual(len(siennes), 1)
            self.assertEqual(autres[0]['objet'], 'Réservé')
            texte = str(autres[0])
            for secret in ('Demandeur', 'demandeur@example.com', 'bob@example.com',
                           'Sujet prive', 'note privee'):
                self.assertNotIn(secret, texte)
            self.assertEqual(siennes[0]['objet'], 'Mon sujet')
        # Le RH, lui, voit tout en détail.
        vue_rh = self.client_de(self.rh).get('/api/reservations/').data
        self.assertTrue(all(not e['lecture_seule'] for e in vue_rh))

    def test_un_manager_ne_peut_pas_reserver_un_creneau_deja_pris(self):
        self.client_de(self.rh).post('/api/reservations/', self.reservation(), format='json')
        reponse = self.client_de(self.manager).post(
            '/api/reservations/', self.reservation(), format='json')
        self.assertEqual(reponse.status_code, 400)

    def test_un_manager_n_a_pas_acces_a_l_administration(self):
        client = self.client_de(self.manager)
        self.assertEqual(client.get('/api/dashboard/stats/').status_code, 403)
        self.assertEqual(client.get('/api/reservations/export/').status_code, 403)
        self.assertEqual(client.get('/api/administration/utilisateurs-rh/').status_code, 403)
        self.assertEqual(client.post('/api/salles/', {'nom_salle': 'X'}, format='json').status_code, 403)
        self.assertEqual(client.patch(
            f'/api/salles/{self.salle.pk}/', {'nom_salle': 'Y'}, format='json').status_code, 403)

    def test_un_manager_peut_consulter_les_salles(self):
        client = self.client_de(self.manager)
        self.assertEqual(client.get('/api/salles/').status_code, 200)
        self.assertEqual(client.get(
            f'/api/salles/disponibles/?date={self.demain}&heure_debut=09:00&heure_fin=10:00'
        ).status_code, 200)

    def test_l_historique_d_un_manager_porte_son_nom(self):
        self.manager.first_name, self.manager.last_name = 'Moussa', 'Diallo'
        self.manager.save()
        rid = self.client_de(self.manager).post(
            '/api/reservations/', self.reservation(), format='json').data['id_reservation']
        vue_rh = self.client_de(self.rh).get(f'/api/reservations/{rid}/').data
        self.assertEqual(vue_rh['created_by_name'], 'Moussa Diallo')


@override_settings(CACHES=CACHE_MEMOIRE)
class ComptesEtSessionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = creer_compte('admin', SUPER_ADMIN_GROUP)
        cls.rh = creer_compte('rh', RH_GROUP)
        cls.manager = creer_compte('mgr', MANAGER_GROUP)

    def setUp(self):
        cache.clear()  # les compteurs de limitation ne doivent pas fuir d'un test à l'autre

    def connexion(self, email='rh@example.com', mot_de_passe=MOT_DE_PASSE):
        return APIClient().post(
            '/api/login/', {'email': email, 'password': mot_de_passe}, format='json',
        )

    def test_connexion_par_email_sans_tenir_compte_des_majuscules(self):
        self.assertEqual(self.connexion('rh@example.com').status_code, 200)
        reponse = self.connexion('  RH@Example.COM ')
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data['role'], RH_GROUP)

    def test_le_role_est_lu_cote_serveur_pour_chaque_profil(self):
        for email, role in (('admin@example.com', SUPER_ADMIN_GROUP),
                            ('rh@example.com', RH_GROUP),
                            ('mgr@example.com', MANAGER_GROUP)):
            self.assertEqual(self.connexion(email).data['role'], role)

    def test_le_nom_d_utilisateur_ne_sert_plus_a_se_connecter(self):
        reponse = APIClient().post(
            '/api/login/', {'username': 'rh', 'password': MOT_DE_PASSE}, format='json')
        self.assertEqual(reponse.status_code, 401)

    def test_message_unique_en_cas_d_echec(self):
        mauvais_mdp = self.connexion(mot_de_passe='faux')
        inconnu = self.connexion('inconnu@example.com')
        sans_role = creer_compte('sansrole', 'AUTRE')
        sans_role.groups.clear()
        pas_de_role = self.connexion('sansrole@example.com')
        self.rh.is_active = False
        self.rh.save()
        inactif = self.connexion()
        messages = {
            str(r.data.get('detail'))
            for r in (mauvais_mdp, inconnu, pas_de_role, inactif)
        }
        self.assertEqual(len(messages), 1)

    def test_un_jeton_par_appareil_et_deconnexion_ciblee(self):
        jeton_a = self.connexion().data['token']
        jeton_b = self.connexion().data['token']
        self.assertNotEqual(jeton_a, jeton_b)
        self.assertEqual(JetonAppareil.objects.filter(utilisateur=self.rh).count(), 2)

        appareil_a, appareil_b = APIClient(), APIClient()
        appareil_a.credentials(HTTP_AUTHORIZATION=f'Token {jeton_a}')
        appareil_b.credentials(HTTP_AUTHORIZATION=f'Token {jeton_b}')
        self.assertEqual(appareil_a.get('/api/me/').status_code, 200)
        self.assertEqual(appareil_a.post('/api/logout/').status_code, 200)
        self.assertEqual(appareil_a.get('/api/me/').status_code, 401)
        self.assertEqual(appareil_b.get('/api/me/').status_code, 200)

    def test_limite_de_tentatives_par_adresse_email(self):
        statuts = [self.connexion(mot_de_passe='faux').status_code for _ in range(8)]
        self.assertIn(429, statuts)

    def admin_client(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        return client

    def test_desactivation_d_un_rh_avec_chaine_false_coupe_les_acces(self):
        jeton = self.connexion().data['token']
        reponse = self.admin_client().patch(
            f'/api/administration/utilisateurs-rh/{self.rh.pk}/', {'actif': 'false'}, format='json')
        self.assertEqual(reponse.status_code, 200, getattr(reponse, 'data', None))
        self.rh.refresh_from_db()
        self.assertFalse(self.rh.is_active)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {jeton}')
        self.assertEqual(client.get('/api/me/').status_code, 401)

    def test_valeur_booleenne_invalide_refusee(self):
        reponse = self.admin_client().patch(
            f'/api/administration/utilisateurs-rh/{self.rh.pk}/', {'actif': 'peut-etre'}, format='json')
        self.assertEqual(reponse.status_code, 400)

    def test_le_super_admin_cree_un_compte_manager_par_email(self):
        reponse = self.admin_client().post('/api/administration/utilisateurs-rh/', {
            'email': 'Nouveau.Manager@Example.com', 'nom': 'Traore', 'prenom': 'Issa',
            'password': 'Un-mot-de-passe-solide-9', 'role': 'MANAGER',
        }, format='json')
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(reponse.data['role'], MANAGER_GROUP)
        self.assertEqual(reponse.data['email'], 'nouveau.manager@example.com')
        connexion = self.connexion('nouveau.manager@example.com', 'Un-mot-de-passe-solide-9')
        self.assertEqual(connexion.status_code, 200)
        self.assertEqual(connexion.data['role'], MANAGER_GROUP)
        liste = self.admin_client().get('/api/administration/utilisateurs-rh/').data
        self.assertIn(MANAGER_GROUP, {u['role'] for u in liste})

    def test_role_invalide_ou_email_deja_pris_refuse(self):
        client = self.admin_client()
        base = {'email': 'x@example.com', 'password': 'Un-mot-de-passe-solide-9'}
        self.assertEqual(client.post(
            '/api/administration/utilisateurs-rh/', {**base, 'role': 'SUPER_ADMIN'},
            format='json').status_code, 400)
        self.assertEqual(client.post(
            '/api/administration/utilisateurs-rh/', {**base, 'email': 'RH@example.com'},
            format='json').status_code, 400)

    def test_changer_le_role_coupe_les_sessions_et_change_les_droits(self):
        jeton = self.connexion('mgr@example.com').data['token']
        reponse = self.admin_client().patch(
            f'/api/administration/utilisateurs-rh/{self.manager.pk}/', {'role': 'RH'}, format='json')
        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertEqual(reponse.data['role'], RH_GROUP)
        ancien = APIClient()
        ancien.credentials(HTTP_AUTHORIZATION=f'Token {jeton}')
        self.assertEqual(ancien.get('/api/me/').status_code, 401)
        self.assertEqual(self.connexion('mgr@example.com').data['role'], RH_GROUP)

    @skipUnless(connection.vendor in ('postgresql', 'sqlite'), "index d'unicité non géré sous MySQL")
    def test_l_unicite_de_l_email_est_garantie_par_la_base(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            get_user_model().objects.create_user(
                username='doublon', email='RH@EXAMPLE.COM', password=MOT_DE_PASSE)


@override_settings(CACHES=CACHE_MEMOIRE)
class DeploiementTests(TestCase):
    """Ce dont un cluster (Kubernetes, ingress, sondes) a besoin pour fonctionner."""

    def test_sondes_de_sante_sans_connexion_et_avec_une_adresse_ip_comme_hote(self):
        # Les sondes d'un cluster appellent l'adresse IP du pod, pas le nom de domaine.
        client = Client(HTTP_HOST='10.1.2.3')
        self.assertEqual(client.get('/api/health/').status_code, 200)
        self.assertEqual(client.get('/api/ready/').status_code, 200)

    def test_les_profils_applicatifs_sont_crees_par_migration(self):
        noms = set(Group.objects.values_list('name', flat=True))
        self.assertTrue({SUPER_ADMIN_GROUP, RH_GROUP, MANAGER_GROUP} <= noms)

    def test_un_en_tete_x_forwarded_for_ne_contourne_pas_la_limite_de_connexion(self):
        # Chaque tentative annonce une fausse adresse et un email différent : sans
        # protection, aucune ne serait jamais limitée.
        statuts = [
            APIClient().post(
                '/api/login/', {'email': f'inconnu{i}@example.com', 'password': 'faux'},
                format='json', HTTP_X_FORWARDED_FOR=f'10.9.9.{i}',
            ).status_code
            for i in range(14)
        ]
        self.assertIn(429, statuts)
