from django.urls import reverse
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from app.api_v1.system.serializers import CurrentUserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CurrentUserSerializer
    queryset = User.objects.none()

    def get_object(self):
        return self.request.user


class ApiIndex(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request):
        # todo: use this for global menu? add permissions? or enable only in debug mode?
        return Response([
            {'url': reverse('api_v1:lib-list')},
        ])
