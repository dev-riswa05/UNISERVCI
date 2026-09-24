from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
