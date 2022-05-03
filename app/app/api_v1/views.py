# todo: make errors in one style maybe {"message": "error message"}

from django.urls import reverse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiIndex(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request):
        # todo: use this for global menu? add permissions? or enable only in debug mode?
        return Response([
            {'url': reverse('api_v1:lib-list')},
        ])
