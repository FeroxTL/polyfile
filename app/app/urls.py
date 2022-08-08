from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import PasswordResetView
from django.urls import path, include

from app.views import IndexView, CustomLoginView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('accounts/login/', CustomLoginView.as_view(), name='accounts-login'),
    path('admin/', admin.site.urls),

    path(
        'accounts/reset/',
        PasswordResetView.as_view(template_name='accounts/reset-password.html'),
        name='password_reset'
    ),

    path('api/v1/', include(('app.api_v1.urls', 'api_v1'))),
]


if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns.append(
        path('__debug__/', include('debug_toolbar.urls')),
    )
