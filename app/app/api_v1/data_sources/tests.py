from unittest import mock
from unittest.mock import PropertyMock

from django.forms import forms, fields
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.factories import SuperuserFactory, UserFactory
from app.utils.tests import TestProvider
from storage.factories import DataSourceFactory
from storage.models import DataSource


class DataSourceRegularUserTests(APITestCase):
    """Test regular user data source creation."""
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_data_source_create(self):
        url = reverse('api_v1:ds-list')

        # list
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, response.data)

        # create
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)

    def test_data_source_update(self):
        data_source = DataSourceFactory(data_provider_id=TestProvider.provider_id)
        url = reverse('api_v1:ds-detail', args=[data_source.pk])
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, 403)


class DataSourceTests(APITestCase):
    def setUp(self) -> None:
        self.user = SuperuserFactory()
        self.client.force_login(self.user)

    def test_data_source_create(self):
        url = reverse('api_v1:ds-list')
        data = {
            'name': 'Foo',
            'data_provider_id': TestProvider.provider_id,
            'options': {'foo': 'bar'},
        }

        # list
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # create
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DataSource.objects.count(), 1)
        ds = DataSource.objects.get()
        self.assertEqual(ds.name, 'Foo')
        self.assertEqual(ds.data_provider_id, TestProvider.provider_id)
        self.assertDictEqual(ds.options_dict, {'foo': 'bar'})

        # no such data_provider_id
        data = {
            'name': 'Foo',
            'data_provider_id': 'does-not-exist',
            'options': {},
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'data_provider_id': ['"does-not-exist" is not a valid choice.']})

    class MyForm(forms.Form):
        foo = fields.CharField(required=True, min_length=2)

    def test_data_source_create_with_validation(self):
        url = reverse('api_v1:ds-list')
        data = {
            'name': 'Foo',
            'data_provider_id': TestProvider.provider_id,
            'options': {},
        }
        with mock.patch.object(TestProvider, 'validation_class', new_callable=PropertyMock) as p:
            p.return_value = self.MyForm
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'options': {'foo': ['This field is required.']}})

        # invalid data
        data = {
            'name': 'Foo',
            'data_provider_id': TestProvider.provider_id,
            'options': {'foo': '1'},
        }
        with mock.patch.object(TestProvider, 'validation_class', new_callable=PropertyMock) as p:
            p.return_value = self.MyForm
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'options': {'foo': [
            'Ensure this value has at least 2 characters (it has 1).'
        ]}})

        # valid data
        data = {
            'name': 'Foo',
            'data_provider_id': TestProvider.provider_id,
            'options': {'foo': 'bar'},
        }
        with mock.patch.object(TestProvider, 'validation_class', new_callable=PropertyMock) as p:
            p.return_value = self.MyForm
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        ds = DataSource.objects.get()
        self.assertDictEqual(ds.options_dict, {'foo': 'bar'})

    def test_data_source_update(self):
        # put
        data_source = DataSourceFactory(data_provider_id=TestProvider.provider_id)
        url = reverse('api_v1:ds-detail', args=[data_source.pk])
        data = {
            'name': 'Foo',
            'data_provider_id': TestProvider.provider_id,
            'options': {},
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        # patch
        data = {'name': 'FooBar'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        data_source.refresh_from_db()
        self.assertEqual(data_source.name, 'FooBar')
