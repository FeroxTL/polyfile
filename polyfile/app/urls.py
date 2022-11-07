from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from app.views import (
    IndexView, CustomLoginView, CustomPasswordResetView, CustomPasswordResetConfirmView, CustomPasswordResetDoneView,
    CustomPasswordResetCompleteView
)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('accounts/login/', CustomLoginView.as_view(), name='accounts-login'),
    path('admin/', admin.site.urls),

    path('accounts/reset_password/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('accounts/password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/password_reset/complete/', CustomPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    path('api/v1/', include(('app.api_v1.urls', 'api_v1'))),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.ENABLE_DEBUG_TOOLBAR:  # noqa
    urlpatterns.append(
        path('__debug__/', include('debug_toolbar.urls')),
    )
