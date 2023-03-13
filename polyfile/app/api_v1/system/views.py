from django.urls import reverse
from rest_framework import generics, permissions, response, views

from polyfile.accounts.models import User
from polyfile.app.api_v1.system.serializers import CurrentUserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    """Current user info."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CurrentUserSerializer
    queryset = User.objects.none()

    def get_object(self):
        """Return the object the view is displaying."""
        return self.request.user


class ApiIndex(views.APIView):
    """Information about available APIs for user."""
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request):
        """Retrieve api views list."""
        return response.Response([
            {
                'url': reverse('api_v1:lib-list'),
                'name': 'My libraries',
            },
        ])
