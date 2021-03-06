from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.factories import SuperuserFactory, UserFactory
from storage.data_providers.base import provider_registry


class DataProviderTests(APITestCase):
    def setUp(self) -> None:
        self.user = SuperuserFactory()
        self.client.force_login(self.user)

    def test_data_provider_list(self):
        url = reverse('api_v1:dp-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(provider_registry.providers))

        # anonymous
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # regular user
        self.client.force_login(UserFactory())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
