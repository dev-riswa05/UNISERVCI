from django.urls import path

from .views import (
    SalleListCreateView,
    SallesDisponiblesView,
    ReservationListCreateView,
    ReservationDetailView,
    AnnulerReservationView,
    PlanningReservationsView,
    AffichageSallesView,
    DashboardStatsView, ProfilRHAdminView, SalleDetailView,
    DupliquerReservationView, ExportReservationsView,
    RHUserListCreateView, RHUserDetailView, RHUserResendAccessView,
)

urlpatterns = [
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('administration/profils-rh/', ProfilRHAdminView.as_view(), name='admin-profils-rh'),
    path('administration/utilisateurs-rh/', RHUserListCreateView.as_view(), name='admin-rh-users'),
    path('administration/utilisateurs-rh/<int:pk>/', RHUserDetailView.as_view(), name='admin-rh-user'),
    path('administration/utilisateurs-rh/<int:pk>/renvoyer-acces/', RHUserResendAccessView.as_view(), name='admin-rh-resend'),
    path('reservations/export/', ExportReservationsView.as_view(), name='export-reservations'),
    path(
        'affichage/',
        AffichageSallesView.as_view(),
        name='affichage-salles'
    ),
    path(
        'salles/',
        SalleListCreateView.as_view(),
        name='salles'
    ),
    path('salles/<int:pk>/', SalleDetailView.as_view(), name='salle-detail'),

    path(
        'salles/disponibles/',
        SallesDisponiblesView.as_view(),
        name='salles-disponibles'
    ),

    path(
        'reservations/',
        ReservationListCreateView.as_view(),
        name='reservations'
    ),

    path(
        'reservations/<int:pk>/',
        ReservationDetailView.as_view(),
        name='reservation-detail'
    ),

    path(
        'reservations/<int:pk>/annuler/',
        AnnulerReservationView.as_view(),
        name='annuler-reservation'
    ),
    path('reservations/<int:pk>/dupliquer/', DupliquerReservationView.as_view(), name='dupliquer-reservation'),

    path(
        'planning/',
        PlanningReservationsView.as_view(),
        name='planning-reservations'
    ),
]
