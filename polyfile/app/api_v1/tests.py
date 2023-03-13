from django.contrib import auth
from django.urls import reverse
from django.test import TestCase
from rest_framework import status

from polyfile.accounts.factories import UserFactory


class AuthTests(TestCase):
    def test_user_logout(self):
        """Ensure we can log out."""
        self.user = UserFactory()
        self.client.force_login(self.user, backend='django.contrib.auth.backends.ModelBackend')
        url = reverse('api_v1:logout')

        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
