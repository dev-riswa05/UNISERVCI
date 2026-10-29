from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.db.models import Count, Prefetch, Sum
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
import csv
import logging

logger = logging.getLogger(__name__)

from .models import (
    Salles,
    Reservations,
    Participants,
    Rappels,
    Utilisateurs,
    ProfilRH,
    Notifications,
)

from .serializers import (
    SalleSerializer,
    ReservationSerializer,
    AffichageReservationSerializer,
    AffichageSalleSerializer,
)

from .horaires import FERMETURE, OUVERTURE
from .emails import envoyer_annulation_reservation, envoyer_email_acces_rh, envoyer_email_en_arriere_plan
from .authentication import request_rh_profile
from .permissions import (
    IsRH, IsRHOrManager, IsSuperAdmin, RH_GROUP, ROLES_COMPTES,
    est_proprietaire, gere_toutes_les_reservations, user_role,
)


def utilisateur_metier_pour(user):
    """Retourne le compte métier correspondant au compte Django connecté.

    Le compte métier est créé au besoin à partir de l'email du compte Django :
    une réservation n'est jamais attribuée à un utilisateur arbitraire.
    """
    if not user.email:
        return None
    utilisateur = Utilisateurs.objects.filter(
        email__iexact=user.email,
        actif=True
    ).first()
    if utilisateur:
        return utilisateur
    if Utilisateurs.objects.filter(email__iexact=user.email).exists():
        return None  # compte métier existant mais désactivé
    return Utilisateurs.objects.create(
        nom=user.last_name or user.get_username(),
        prenom=user.first_name,
        email=user.email,
        mot_de_passe='!',
        role=user_role(user),
        actif=True,
        date_creation=timezone.now(),
    )


def valeur_booleenne(valeur, champ):
    """Convertit une valeur JSON/formulaire en booléen, sinon erreur 400."""
    if isinstance(valeur, bool):
        return valeur
    if isinstance(valeur, str) and valeur.lower() in ('true', 'false'):
        return valeur.lower() == 'true'
    raise ValidationError({champ: 'Une valeur booléenne est obligatoire.'})


FORMULE_DEBUTS = ('=', '+', '-', '@', chr(9), chr(13))


def neutraliser_formule(valeur):
    """Empêche Excel d'exécuter une cellule CSV commençant par une formule."""
    texte = '' if valeur is None else str(valeur)
    if texte and texte[0] in FORMULE_DEBUTS:
        return "'" + texte
    return texte


def revoquer_sessions(user):
    """Coupe immédiatement tous les accès actifs d'un compte."""
    Token.objects.filter(user=user).delete()
    user.jetons_appareil.all().delete()
    user.sessions_rh.filter(actif=True).update(actif=False)


# ==========================================================
# VUE ÉCRAN PUBLIQUE (LECTURE SEULE, SANS CONNEXION)
# ==========================================================

class AffichageThrottle(AnonRateThrottle):
    scope = 'affichage'


class AffichageSallesView(APIView):
    """Flux minimal pour les écrans : toutes les salles, sans donnée personnelle.

    Public : aucune authentification. Seuls la salle, l'horaire et un objet
    générique sont exposés ; jamais de nom, d'email ni de note.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AffichageThrottle]

    def get(self, request):
        date_param = request.query_params.get('date')
        id_salle = request.query_params.get('id_salle')

        if id_salle and not id_salle.isdigit():
            return Response(
                {"erreur": "L'identifiant de salle est invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if date_param:
            date_affichage = parse_date(date_param)
            if date_affichage is None:
                return Response(
                    {"erreur": "La date est invalide."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date_affichage = timezone.localdate()

        salles = Salles.objects.filter(active=True).order_by('nom_salle')
        reservations = Reservations.objects.filter(
            date_reservation=date_affichage
        ).exclude(statut='ANNULEE')

        if id_salle:
            reservations = reservations.filter(id_salle=id_salle)

        reservations = reservations.select_related('id_salle').order_by(
            'heure_debut'
        )

        return Response({
            'date': date_affichage,
            'salles': AffichageSalleSerializer(salles, many=True).data,
            'reservations': AffichageReservationSerializer(
                reservations,
                many=True
            ).data,
        })


# ==========================================================
# SALLES
# ==========================================================

class SalleListCreateView(generics.ListCreateAPIView):
    queryset = Salles.objects.all()
    serializer_class = SalleSerializer
    def get_permissions(self):
        return [(IsSuperAdmin if self.request.method == 'POST' else IsRHOrManager)()]

    def perform_create(self, serializer):
        serializer.save(date_creation=timezone.now())




class SallesDisponiblesView(APIView):
    permission_classes = [IsRHOrManager]

    def get(self, request):

        date = request.query_params.get('date')
        heure_debut = request.query_params.get('heure_debut')
        heure_fin = request.query_params.get('heure_fin')
        reservation_a_exclure = request.query_params.get(
            'exclure_reservation'
        )

        if not date or not heure_debut or not heure_fin:
            return Response(
                {
                    "erreur": (
                        "Les paramètres date, heure_debut "
                        "et heure_fin sont obligatoires."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ne jamais comparer directement les chaînes reçues : parse_time
        # refuse aussi les formats invalides avant d'interroger MySQL.
        date_validee = parse_date(date)
        debut_valide = parse_time(heure_debut)
        fin_valide = parse_time(heure_fin)

        if not date_validee or not debut_valide or not fin_valide:
            return Response(
                {"erreur": "La date ou les heures sont invalides."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if debut_valide >= fin_valide:
            return Response(
                {
                    "erreur": (
                        "L'heure de fin doit être après "
                        "l'heure de début."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reservations_en_conflit = Reservations.objects.filter(
            date_reservation=date_validee,
            heure_debut__lt=fin_valide,
            heure_fin__gt=debut_valide
        ).exclude(
            statut='ANNULEE'
        )

        # En modification, la réservation courante ne doit pas entrer en
        # conflit avec elle-même. Les autres conflits restent bien détectés.
        if reservation_a_exclure and not reservation_a_exclure.isdigit():
            return Response(
                {"erreur": "L'identifiant de réservation est invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reservation_a_exclure:
            reservations_en_conflit = reservations_en_conflit.exclude(
                id_reservation=reservation_a_exclure
            )

        if debut_valide < OUVERTURE or fin_valide > FERMETURE:
            return Response(
                {
                    "erreur": (
                        "Le créneau doit être compris entre 08h00 et 17h30."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        salles_occupees = reservations_en_conflit.values_list(
            'id_salle_id',
            flat=True
        )

        salles_disponibles = Salles.objects.filter(
            active=True
        ).exclude(
            id_salle__in=salles_occupees
        )

        serializer = SalleSerializer(
            salles_disponibles,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# ==========================================================
# LISTE ET CREATION DES RESERVATIONS
# ==========================================================

def verifier_acces_reservation(user, reservation):
    """Un manager n'agit que sur ses propres réservations (RH/Super Admin : toutes)."""
    if not gere_toutes_les_reservations(user) and not est_proprietaire(user, reservation):
        raise PermissionDenied("Vous ne pouvez agir que sur vos propres réservations.")


def reservations_detaillees():
    """Réservations avec leurs relations préchargées (évite le N+1)."""
    return Reservations.objects.select_related(
        'id_salle', 'created_by', 'updated_by', 'cancelled_by'
    ).prefetch_related(
        'participants_set',
        Prefetch(
            'notifications_set',
            queryset=Notifications.objects.only('id_notification', 'id_reservation', 'statut'),
        ),
    )


class PaginationFacultative(PageNumberPagination):
    """Paginée seulement si le client envoie `page` ou `page_size`.

    Sans ces paramètres la réponse reste une simple liste : l'application
    actuelle continue de fonctionner, et les gros volumes peuvent être
    récupérés page par page (`?page=1&page_size=50`).
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

    def paginate_queryset(self, queryset, request, view=None):
        if 'page' not in request.query_params and 'page_size' not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)


class ReservationListCreateView(generics.ListCreateAPIView):
    queryset = reservations_detaillees().order_by('id_reservation')
    pagination_class = PaginationFacultative
    serializer_class = ReservationSerializer
    permission_classes = [IsRHOrManager]

    def perform_create(self, serializer):
        """Associe la réservation au RH côté serveur, jamais côté React."""
        utilisateur_metier = utilisateur_metier_pour(self.request.user)

        if utilisateur_metier is None:
            raise ValidationError({
                "id_utilisateur": (
                    "Aucun profil RH métier actif n'est associé à ce compte."
                )
            })

        serializer.save(
            id_utilisateur=utilisateur_metier,
            statut='CONFIRMEE',
            created_by=request_rh_profile(self.request),
            created_at=timezone.now(),
        )


# ==========================================================
# CONSULTATION ET MODIFICATION D'UNE RESERVATION
# ==========================================================

class ReservationDetailView(generics.RetrieveUpdateAPIView):
    queryset = reservations_detaillees()
    serializer_class = ReservationSerializer
    permission_classes = [IsRHOrManager]

    lookup_field = 'id_reservation'
    lookup_url_kwarg = 'pk'

    def get_object(self):
        reservation = super().get_object()
        verifier_acces_reservation(self.request.user, reservation)
        return reservation

    def perform_update(self, serializer):
        # Une annulation constitue l'état final dans la V1. Cela protège
        # l'historique même si quelqu'un appelle directement l'API.
        if serializer.instance.statut == 'ANNULEE':
            raise ValidationError(
                "Une réservation annulée ne peut plus être modifiée."
            )
        serializer.save(
            updated_by=request_rh_profile(self.request),
            updated_at=timezone.now(),
        )


# ==========================================================
# ANNULATION D'UNE RESERVATION
# ==========================================================

class AnnulerReservationView(APIView):
    permission_classes = [IsRHOrManager]

    def post(self, request, pk):

        try:
            reservation = Reservations.objects.get(
                id_reservation=pk
            )

        except Reservations.DoesNotExist:
            return Response(
                {
                    "erreur": "Réservation introuvable."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        verifier_acces_reservation(request.user, reservation)

        if reservation.statut == "ANNULEE":
            return Response(
                {
                    "message": "Cette réservation est déjà annulée."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # La réservation et son rappel changent d'état dans la même
        # transaction : ils ne peuvent donc jamais se contredire.
        with transaction.atomic():
            # Verrou : deux annulations simultanées n'envoient qu'un seul e-mail.
            reservation = Reservations.objects.select_for_update().select_related(
                'id_salle'
            ).get(id_reservation=pk)
            if reservation.statut == "ANNULEE":
                return Response(
                    {"message": "Cette réservation est déjà annulée."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            reservation.statut = "ANNULEE"
            reservation.cancelled_by = request_rh_profile(request)
            reservation.cancelled_at = timezone.now()
            reservation.save(update_fields=["statut", "cancelled_by", "cancelled_at"])

            Rappels.objects.filter(
                id_reservation=reservation,
                statut='EN_ATTENTE'
            ).update(statut='ANNULE')

            participant_ids = list(
                Participants.objects.filter(
                    id_reservation=reservation
                ).values_list('id_participant', flat=True)
            )

            # L'e-mail part seulement après validation du COMMIT. `robust`
            # évite qu'une panne SMTP transforme une annulation réussie en 500.
            # On matérialise les destinataires avant de rendre la réponse, puis
            # l'envoi SMTP se poursuit hors du cycle HTTP. Une connexion SMTP
            # lente ne bloque donc plus l'annulation à l'écran.
            participants_a_prevenir = list(
                Participants.objects.filter(id_participant__in=participant_ids)
            )
            transaction.on_commit(
                lambda: envoyer_email_en_arriere_plan(
                    lambda: envoyer_annulation_reservation(
                        reservation, participants_a_prevenir
                    )
                ),
                robust=True
            )

        return Response(
            {
                "message": "Réservation annulée avec succès.",
                "id_reservation": reservation.id_reservation,
                "statut": reservation.statut
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# PLANNING DES RESERVATIONS
# ==========================================================

class PlanningReservationsView(APIView):
    permission_classes = [IsRHOrManager]

    def get(self, request):

        date = request.query_params.get('date')
        id_salle = request.query_params.get('id_salle')

        if date and parse_date(date) is None:
            raise ValidationError({'date': 'La date est invalide.'})
        if id_salle and not id_salle.isdigit():
            raise ValidationError({
                'id_salle': "L'identifiant de salle est invalide."
            })

        reservations = reservations_detaillees().exclude(
            statut='ANNULEE'
        )

        if date:
            reservations = reservations.filter(
                date_reservation=date
            )

        if id_salle:
            reservations = reservations.filter(
                id_salle=id_salle
            )

        reservations = reservations.order_by(
            'date_reservation',
            'heure_debut'
        )

        serializer = ReservationSerializer(
            reservations,
            many=True,
            context={'request': request}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class DashboardStatsView(APIView):
    """Indicateurs calculés côté serveur pour conserver une source fiable."""
    permission_classes = [IsRH]

    def get(self, request):
        today = timezone.localdate()
        active = Reservations.objects.exclude(statut='ANNULEE')
        today_qs = active.filter(date_reservation=today)
        by_room = list(active.values(
            'id_salle', 'id_salle__nom_salle'
        ).annotate(total=Count('id_reservation')).order_by('-total')[:5])
        recent = ReservationSerializer(
            Reservations.objects.select_related(
                'id_salle', 'created_by', 'updated_by', 'cancelled_by'
            ).order_by('-created_at', '-id_reservation')[:8], many=True
        ).data
        return Response({
            'today': today_qs.count(),
            'upcoming': active.filter(date_reservation__gte=today).count(),
            'participants_today': today_qs.aggregate(
                total=Sum('nombre_participants')
            )['total'] or 0,
            'cancelled': Reservations.objects.filter(statut='ANNULEE').count(),
            'rooms': Salles.objects.filter(active=True).count(),
            'by_room': by_room,
            'recent_activity': recent,
        })


class ProfilRHAdminView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response(list(ProfilRH.objects.values('id', 'nom', 'actif', 'date_creation')))

    def post(self, request):
        nom = (request.data.get('nom') or '').strip().upper()
        if not nom:
            raise ValidationError({'nom': 'Le nom du profil est obligatoire.'})
        profil, created = ProfilRH.objects.get_or_create(nom=nom)
        if not created and not profil.actif:
            profil.actif = True; profil.save(update_fields=['actif'])
        return Response({'id': profil.id, 'nom': profil.nom, 'actif': profil.actif}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def patch(self, request):
        try:
            profil = ProfilRH.objects.get(pk=request.data.get('id'))
        except (ProfilRH.DoesNotExist, ValueError, TypeError):
            raise ValidationError({'id': 'Profil RH introuvable.'})
        actif = request.data.get('actif')
        if not isinstance(actif, bool):
            raise ValidationError({'actif': 'Une valeur booléenne est obligatoire.'})
        profil.actif = actif
        profil.save(update_fields=['actif'])
        if not profil.actif:
            profil.sessions.filter(actif=True).update(actif=False)
        return Response({'id': profil.id, 'nom': profil.nom, 'actif': profil.actif})


class SalleDetailView(generics.RetrieveUpdateAPIView):
    queryset = Salles.objects.all()
    serializer_class = SalleSerializer
    def get_permissions(self):
        return [(IsSuperAdmin if self.request.method in ('PUT', 'PATCH') else IsRHOrManager)()]
    lookup_field = 'id_salle'
    lookup_url_kwarg = 'pk'


class DupliquerReservationView(APIView):
    permission_classes = [IsRHOrManager]

    def post(self, request, pk):
        try:
            source = reservations_detaillees().get(pk=pk)
        except Reservations.DoesNotExist:
            return Response({'erreur': 'Réservation introuvable.'}, status=404)
        verifier_acces_reservation(request.user, source)
        data = ReservationSerializer(source, context={'request': request}).data
        for key in ('id_reservation', 'statut', 'created_by_name', 'created_at', 'updated_by_name', 'updated_at', 'cancelled_by_name', 'cancelled_at'):
            data.pop(key, None)
        data['date_reservation'] = request.data.get('date_reservation', data['date_reservation'])
        serializer = ReservationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        utilisateur = utilisateur_metier_pour(request.user)
        if utilisateur is None:
            raise ValidationError({
                'id_utilisateur': (
                    "Aucun profil RH métier actif n'est associé à ce compte."
                )
            })
        duplicate = serializer.save(id_utilisateur=utilisateur, statut='CONFIRMEE', created_by=request_rh_profile(request), created_at=timezone.now())
        return Response(ReservationSerializer(duplicate, context={'request': request}).data, status=201)


class ExportReservationsView(APIView):
    permission_classes = [IsRH]

    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="reservations-uniserv.csv"'
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Date', 'Début', 'Fin', 'Salle', 'Objet', 'Demandeur', 'Statut', 'Créée par'])
        reservations = Reservations.objects.select_related('id_salle', 'created_by').order_by('-date_reservation', '-heure_debut')
        for item in reservations.iterator(chunk_size=500):
            writer.writerow([item.date_reservation, item.heure_debut, item.heure_fin, neutraliser_formule(item.id_salle.nom_salle), neutraliser_formule(item.objet), neutraliser_formule(item.nom_demandeur), item.statut, neutraliser_formule(item.created_by.nom if item.created_by else '')])
        return response


def serialize_rh_user(user):
    return {
        'id': user.id, 'nom': user.last_name, 'prenom': user.first_name,
        'username': user.username, 'email': user.email, 'role': user_role(user),
        'actif': user.is_active, 'date_creation': user.date_joined,
    }


class RHUserListCreateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        users = get_user_model().objects.filter(
            groups__name__in=ROLES_COMPTES
        ).distinct().order_by('email', 'username')
        return Response([serialize_rh_user(user) for user in users])

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        # L'email est l'identifiant de connexion ; le nom d'utilisateur Django
        # n'est qu'un identifiant interne et reprend l'email par défaut.
        username = (request.data.get('username') or '').strip() or email
        if not email:
            raise ValidationError({'email': "L'adresse email est obligatoire."})
        role = (request.data.get('role') or RH_GROUP).upper()
        if role not in ROLES_COMPTES:
            raise ValidationError({'role': "Rôle invalide : choisissez RH ou MANAGER."})
        try:
            validate_email(email)
        except DjangoValidationError:
            raise ValidationError({'email': 'Saisissez une adresse email valide.'})
        model = get_user_model()
        if model.objects.filter(username__iexact=username).exists():
            raise ValidationError({'username': "Ce nom d'utilisateur est déjà utilisé."})
        if model.objects.filter(email__iexact=email).exists():
            raise ValidationError({'email': "Cette adresse email est déjà utilisée."})
        password = request.data.get('password') or ''
        if not password:
            raise ValidationError({'password': 'Le mot de passe de connexion est obligatoire.'})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise ValidationError({'password': list(exc.messages)})
        user = model(username=username, email=email,
                     first_name=(request.data.get('prenom') or '').strip(),
                     last_name=(request.data.get('nom') or '').strip(),
                     is_active=valeur_booleenne(request.data.get('actif', True), 'actif'))
        user.set_password(password); user.save()
        user.groups.add(Group.objects.get_or_create(name=role)[0])
        Utilisateurs.objects.get_or_create(
            email=email,
            defaults={'nom': user.last_name or username, 'prenom': user.first_name,
                      'mot_de_passe': '!', 'role': role,
                      'actif': user.is_active, 'date_creation': timezone.now()}
        )
        email_sent = True
        try:
            envoyer_email_acces_rh(user)
        except Exception:
            logger.exception("Envoi de l'email d'accès RH impossible.")
            email_sent = False
        message = ('Compte créé avec succès.' if email_sent else
                   "Compte créé avec succès, mais l'email d'accès n'a pas pu être envoyé.")
        return Response({**serialize_rh_user(user), 'email_envoye': email_sent, 'message': message}, status=201)


class RHUserDetailView(APIView):
    permission_classes = [IsSuperAdmin]

    def _get(self, pk):
        try:
            return get_user_model().objects.get(pk=pk, groups__name__in=ROLES_COMPTES)
        except get_user_model().DoesNotExist:
            raise ValidationError({'id': 'Membre RH introuvable.'})

    def get(self, request, pk):
        return Response(serialize_rh_user(self._get(pk)))

    def patch(self, request, pk):
        user = self._get(pk)
        role_change = False
        for field, source in [('first_name', 'prenom'), ('last_name', 'nom')]:
            if source in request.data:
                setattr(user, field, (request.data[source] or '').strip())
        if 'username' in request.data:
            value = (request.data['username'] or '').strip()
            if get_user_model().objects.exclude(pk=pk).filter(username__iexact=value).exists():
                raise ValidationError({'username': "Ce nom d'utilisateur est déjà utilisé."})
            user.username = value
        if 'email' in request.data:
            value = (request.data['email'] or '').strip().lower()
            if get_user_model().objects.exclude(pk=pk).filter(email__iexact=value).exists():
                raise ValidationError({'email': "Cette adresse email est déjà utilisée."})
            user.email = value
        if 'role' in request.data:
            nouveau_role = str(request.data['role']).upper()
            if nouveau_role not in ROLES_COMPTES:
                raise ValidationError({'role': "Rôle invalide : choisissez RH ou MANAGER."})
            if user_role(user) != nouveau_role:
                user.groups.remove(*Group.objects.filter(name__in=ROLES_COMPTES))
                user.groups.add(Group.objects.get_or_create(name=nouveau_role)[0])
                role_change = True
        if 'actif' in request.data:
            user.is_active = valeur_booleenne(request.data['actif'], 'actif')
        if request.data.get('password'):
            try:
                validate_password(request.data['password'], user)
            except DjangoValidationError as exc:
                raise ValidationError({'password': list(exc.messages)})
            user.set_password(request.data['password'])
            mot_de_passe_change = True
        else:
            mot_de_passe_change = False
        user.save()
        Utilisateurs.objects.filter(email__iexact=user.email).update(
            nom=user.last_name or user.username, prenom=user.first_name,
            actif=user.is_active, role=user_role(user))
        if not user.is_active or mot_de_passe_change or role_change:
            revoquer_sessions(user)
        return Response(serialize_rh_user(user))

    def delete(self, request, pk):
        user = self._get(pk)
        email = user.email
        with transaction.atomic():
            # Préserve l'historique des réservations dans la table métier.
            revoquer_sessions(user)
            user.delete()
            if email:
                Utilisateurs.objects.filter(email__iexact=email).update(actif=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RHUserResendAccessView(APIView):
    permission_classes = [IsSuperAdmin]
    def post(self, request, pk):
        try:
            user = get_user_model().objects.get(pk=pk, groups__name__in=ROLES_COMPTES)
            envoyer_email_acces_rh(user)
        except get_user_model().DoesNotExist:
            raise ValidationError({'id': 'Membre RH introuvable.'})
        except Exception:
            logger.exception("Renvoi de l'email d'accès RH impossible.")
            return Response({'erreur': "L'email d'accès n'a pas pu être envoyé."}, status=503)
        return Response({'message': "Email d'accès envoyé."})
