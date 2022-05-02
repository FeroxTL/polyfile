import tempfile
import uuid
from pathlib import Path
from unittest import mock

from PIL import Image
from django.contrib import auth
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.factories import UserFactory
from storage.data_providers.exceptions import ProviderException
from storage.factories import DataSourceFactory, DataLibraryFactory, FileFactory, DirectoryFactory
from storage.models import DataLibrary, Node


class AuthTests(TestCase):
    def test_user_login(self):
        """Ensure we can log in."""
        password = 'foobar'
        user = UserFactory(password=password)
        url = reverse('accounts-login')
        data = {'username': user.username, 'password': password}

        response = self.client.post(url, data, follow=False)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.headers['Location'], '/')
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_user_logout(self):
        """Ensure we can log out."""
        user = UserFactory()
        self.client.force_login(user)
        url = reverse('api_v1:logout')

        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)


class LibraryTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_create_library(self):
        """Ensure we can create a new NodeLibrary object."""
        data_source = DataSourceFactory()
        url = reverse('api_v1:lib-list')
        data = {'name': 'FooBar', 'data_source': data_source.pk}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        data_library = DataLibrary.objects.get()
        self.assertEqual(data_library.name, 'FooBar')

    def test_list_libraries(self):
        """Ensure we can list our libraries."""
        # another user's library
        DataLibraryFactory()

        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertListEqual(response.json(), [{
            'data_source': data_library.data_source.pk,
            'id': str(data_library.pk),
            'name': data_library.name,
        }])

    def test_update_library(self):
        """Ensure we can update our libraries."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-detail', args=[str(data_library.pk)])
        data = {'name': 'foobar'}

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), {
            'data_source': data_library.data_source.pk,
            'id': str(data_library.pk),
            'name': data['name'],
        })

        data_library.refresh_from_db()
        self.assertEqual(data_library.name, 'foobar')

        # patch request
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)


class NodeTests(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    @staticmethod
    def to_json(data_library: DataLibrary, current_node: Node, child_nodes=None):
        if child_nodes is None:
            child_nodes = current_node.get_children()

        return {
            'current_node': {
                'file_type': current_node.file_type,
                'size': current_node.size,
                'name': current_node.name,
                'mimetype': current_node.mimetype and current_node.mimetype.name,
                'has_preview': False,
            },
            'library': {
                'data_source': data_library.data_source.pk,
                'id': str(data_library.pk),
                'name': data_library.name,
            },
            'nodes': [{
                'file_type': child.file_type,
                'has_preview': False,
                'mimetype': child.mimetype and child.mimetype.name,
                'size': child.size,
                'name': child.name,
            } for child in child_nodes]
        }

    def test_list_nodes(self):
        """Ensure we can list our nodes."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), self.to_json(data_library, data_library.root_dir))

        # directory does not exist
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/dost-not-exists/'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

        # not our data library
        data_library = DataLibraryFactory()
        url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

    def test_list_file_node(self):
        """Ensure we can list files too."""
        data_library = DataLibraryFactory(owner=self.user)
        file = FileFactory(parent=data_library.root_dir)
        url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), self.to_json(data_library, current_node=file, child_nodes=[file]))

    def test_rename_node(self):
        """Ensure we can rename node."""
        data_library = DataLibraryFactory(owner=self.user)
        file = FileFactory(parent=data_library.root_dir)
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})
        data = {'name': 'FooBar'}

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        file.refresh_from_db()
        self.assertEqual(file.name, data['name'])

        # try to rename root directory
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # todo: 400 bad request

        # directory does not exist
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/does-not-exist/'})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

    def test_mkdir(self):
        """Ensure we can create directories."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-mkdir', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        data = {'name': 'FooBar'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        data_library.root_dir.refresh_from_db()
        self.assertEqual(data_library.root_dir.get_children().count(), 1)
        directory = data_library.root_dir.get_children().get()
        self.assertTrue(directory.pk)
        self.assertDictEqual(response.json(), {
            'file_type': Node.FileTypeChoices.DIRECTORY.value,
            'size': 0,
            'mimetype': None,
            'name': data['name'],
            'has_preview': False,
        })

        # mkdir with invalid name
        data = {'name': '..'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'name': ['This name is invalid']})

        # mkdir with invalid parent directory
        url = reverse('api_v1:lib-mkdir', kwargs={'lib_id': str(data_library.pk), 'path': '/does-not-exist/'})
        data = {'name': 'FooBar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Node matching query does not exist.'})

    def test_rm(self):
        """Ensure we can remove our nodes."""
        data_library = DataLibraryFactory(owner=self.user)
        file = FileFactory(parent=data_library.root_dir)

        # rm file
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertEqual(data_library.root_dir.get_children().count(), 0)
        self.assertFalse(Node.objects.filter(pk=file.pk).exists())

        # rm directory
        directory = DirectoryFactory(parent=data_library.root_dir)
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + directory.name + '/'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertEqual(data_library.root_dir.get_children().count(), 0)
        self.assertFalse(Node.objects.filter(pk=directory.pk).exists())

        # rm already removed directory
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Node matching query does not exist.'})

        # rm root directory
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Can not remove root directory'})

        # rm not empty directory
        directory = DirectoryFactory(parent=data_library.root_dir)
        FileFactory(parent=directory)
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + directory.name + '/'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'detail': f'Can not remove "{directory.name}": is not empty'})

    def test_file_upload(self):
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        image = Image.new('RGB', (100, 100))

        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            image.save(tmp_file)
            tmp_file.seek(0)
            response = self.client.post(url, {'file': tmp_file}, format='multipart')
            self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

            tmp_path = Path(tmp_file.name)
            self.assertDictEqual(response.json(), {
                'name': tmp_path.name,
                'file_type': 'file',
                'mimetype': 'image/jpeg',
                'size': tmp_path.stat().st_size,
                'has_preview': False
            })

        # library does not exist
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(uuid.uuid4()), 'path': '/'})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            image.save(tmp_file)
            response = self.client.post(url, {'file': tmp_file}, format='multipart')
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'DataLibrary matching query does not exist.'})

        # path does not exist
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': '/does-not-exist/'})

        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            image.save(tmp_file)
            tmp_file.seek(0)
            response = self.client.post(url, {'file': tmp_file}, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'Node matching query does not exist.'})

        # target path is not directory
        target_node = FileFactory(parent=data_library.root_dir)
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': f'/{target_node.name}'})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            image.save(tmp_file)
            tmp_file.seek(0)
            response = self.client.post(url, {'file': tmp_file}, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'Incorrect node type'})


class ProviderTests(APITestCase):
    """Testing api and provider integration -- errors and exceptions."""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_mkdir(self):
        """Test provider exceptions while creating directories."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-mkdir', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        data = {'name': 'FooBar'}
        with mock.patch('app.utils.tests.TestProvider.mkdir') as p:
            p.side_effect = ProviderException('Something went wrong')
            response = self.client.post(url, data, format='json')
            p.assert_called()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Something went wrong'})

    def test_rm(self):
        """Test provider exceptions on file removal."""
        data_library = DataLibraryFactory(owner=self.user)
        directory = DirectoryFactory(parent=data_library.root_dir)
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + directory.name + '/'})
        with mock.patch('app.utils.tests.TestProvider.rm') as p:
            p.side_effect = ProviderException('Something went wrong')
            response = self.client.delete(url)
            p.assert_called()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Something went wrong'})

    def test_rename_node(self):
        """Test provider exceptions on rename node."""
        data_library = DataLibraryFactory(owner=self.user)
        file = FileFactory(parent=data_library.root_dir)
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})
        data = {'name': 'FooBar'}

        with mock.patch('app.utils.tests.TestProvider.rename') as p:
            p.side_effect = ProviderException('Something went wrong')
            response = self.client.put(url, data, format='json')
            p.assert_called()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        # todo: make errors in single style
        # self.assertDictEqual(response.json(), {'detail': 'Something went wrong'})

    def test_file_upload(self):
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        image = Image.new('RGB', (100, 100))

        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            image.save(tmp_file)
            tmp_file.seek(0)
            with mock.patch('app.utils.tests.TestProvider.upload_file') as p:
                p.side_effect = ProviderException('Something went wrong')
                response = self.client.post(url, {'file': tmp_file}, format='multipart')
                p.assert_called()
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            # todo: make errors in single style
            # self.assertDictEqual(response.json(), {'detail': 'Something went wrong'})
