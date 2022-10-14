from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.factories import UserFactory


class SystemTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_current_user(self):
        """Ensure we can get current user info."""
        url = reverse('api_v1:sys-cuser')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'full_name': self.user.full_name,
            'is_superuser': self.user.is_superuser,
        })

        # anonymous
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
