from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.views.static import serve
from reservations.auth_views import (
    ChangePasswordView,
    CurrentUserView,
    LogoutView,
    ProfilePhotoView,
    RoleLoginView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reservations.urls')),

    path(
        'api/login/',
        RoleLoginView.as_view(),
        name='api-login'
    ),
    path(
        'api/me/',
        CurrentUserView.as_view(),
        name='api-me'
    ),
    path('api/me/password/', ChangePasswordView.as_view(), name='api-change-password'),
    path('api/me/photo/', ProfilePhotoView.as_view(), name='api-profile-photo'),
    path(
        'api/logout/',
        LogoutView.as_view(),
        name='api-logout'
    ),
]

if settings.SERVE_MEDIA:
    # `static()` ne fonctionne que si DEBUG est actif ; `serve` fonctionne aussi en
    # production (photos de profil : faible volume). Pour de gros volumes,
    # préférer un stockage objet ou un serveur web dédié.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
