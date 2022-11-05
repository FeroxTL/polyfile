from django.urls import reverse
from rest_framework import generics, permissions, response, views

from accounts.models import User
from app.api_v1.system.serializers import CurrentUserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CurrentUserSerializer
    queryset = User.objects.none()

    def get_object(self):
        return self.request.user


class ApiIndex(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request):
        return response.Response([
            {
                'url': reverse('api_v1:lib-list'),
                'name': 'My libraries',
            },
        ])
