from django.urls import path

from app.api_auth.views import LogoutView

urlpatterns = [
    path('logout', LogoutView.as_view(), name='logout'),
]
