from django.contrib.auth import logout
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.views import APIView


class LogoutView(APIView):
    """Logout user."""
    permission_classes = []

    def post(self, request):
        logout(request)
        return Response({
            'next_url': reverse('index'),
        })
