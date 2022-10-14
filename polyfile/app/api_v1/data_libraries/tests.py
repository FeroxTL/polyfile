import tempfile
import uuid
from pathlib import Path
from unittest import mock, skip

from PIL import Image
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.factories import UserFactory
from app.utils.tests import with_tempdir
from storage.data_providers.exceptions import ProviderException
from storage.factories import DataSourceFactory, DataLibraryFactory, FileFactory, DirectoryFactory
from storage.models import DataLibrary, Node


class LibraryTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    @with_tempdir
    def test_create_library(self, temp_dir):
        """Ensure we can create a new NodeLibrary object."""
        data_source = DataSourceFactory(options={'location': temp_dir})
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
    def to_json_root(data_library: DataLibrary):
        child_nodes = Node.objects.filter(parent__isnull=True, data_library=data_library)

        return {
            'current_node': {},
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

    @staticmethod
    def to_json_node(current_node: Node, child_nodes=None):
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
                'data_source': current_node.data_library.data_source.pk,
                'id': str(current_node.data_library.pk),
                'name': current_node.data_library.name,
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
        self.assertDictEqual(response.json(), self.to_json_root(data_library))

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

    @with_tempdir
    def test_list_file_node(self, temp_dir):
        """Ensure we can list files too."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        file = FileFactory(data_library=data_library)
        url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), self.to_json_node(current_node=file, child_nodes=[file]))

    @with_tempdir
    def test_rename_node(self, temp_dir):
        """Ensure we can rename node."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        file = FileFactory(data_library=data_library)
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})
        data = {'name': 'FooBar'}

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        file.refresh_from_db()
        self.assertEqual(file.name, data['name'])

        # try to rename root directory
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

        # directory does not exist
        url = reverse('api_v1:lib-rename', kwargs={'lib_id': str(data_library.pk), 'path': '/does-not-exist/'})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

    @with_tempdir
    def test_mkdir(self, temp_dir):
        """Ensure we can create directories."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        url = reverse('api_v1:lib-mkdir', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        data = {'name': 'FooBar'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        directory = Node.objects.get(parent__isnull=True, data_library=data_library)
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

    @with_tempdir
    def test_rm(self, temp_dir):
        """Ensure we can remove our nodes."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        file = FileFactory(data_library=data_library)

        # rm file
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(Node.objects.filter(pk=file.pk).exists())

        # rm directory
        directory = DirectoryFactory(data_library=data_library)
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + directory.name + '/'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(Node.objects.filter(pk=directory.pk).exists())

        # rm already removed directory
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Not found.'})

        # rm root directory
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        self.assertDictEqual(response.json(), {'detail': 'Not found.'})

        # rm not empty directory
        directory = DirectoryFactory(data_library=data_library)
        FileFactory(parent=directory)
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': '/' + directory.name + '/'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertDictEqual(response.json(), {'detail': f'Can not remove "{directory.name}": is not empty'})

    @with_tempdir
    def test_file_upload(self, temp_dir):
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
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
        target_node = FileFactory(data_library=data_library)
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': f'/{target_node.name}'})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            image.save(tmp_file)
            tmp_file.seek(0)
            response = self.client.post(url, {'file': tmp_file}, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'Incorrect node type'})


# todo: incorrect test
@skip('Remove when DataProviders will be removed')
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
