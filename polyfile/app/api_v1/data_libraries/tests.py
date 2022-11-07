import tempfile
import uuid
from pathlib import Path

from PIL import Image
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.factories import UserFactory
from app.utils.tests import with_tempdir
from storage.factories import DataSourceFactory, DataLibraryFactory, FileFactory, DirectoryFactory, ImageFactory
from storage.models import DataLibrary, Node, AltNode
from storage.thumbnailer import thumbnailer


class LibraryTests(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    @staticmethod
    def to_dict(instance: DataLibrary):
        return {'id': str(instance.id), 'name': instance.name, 'data_source': instance.data_source_id}

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

        # anonymous create library
        self.client.logout()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

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

        # anonymous list directories
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_update_library(self):
        """Ensure we can update our libraries."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('api_v1:lib-detail', args=[str(data_library.pk)])
        data = {'name': 'foobar'}

        # get library
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), self.to_dict(data_library))

        # update library
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

        # anonymous update
        self.client.logout()
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # anonymous get
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)


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
                'data_source': data_library.data_source_id,
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
    def to_json_node(current_node: Node, child_nodes=None):  # noqa
        if child_nodes is None:
            child_nodes = current_node.get_children()

        return {
            'current_node': {
                'file_type': str(current_node.file_type),
                'size': current_node.size,
                'name': current_node.name,
                'mimetype': current_node.mimetype and current_node.mimetype.name,
                'has_preview': thumbnailer.can_get_thumbnail(current_node.get_mimetype()),
            },
            'library': {
                'data_source': current_node.data_library.data_source.pk,
                'id': str(current_node.data_library.pk),
                'name': current_node.data_library.name,
            },
            'nodes': [{
                'file_type': child.file_type,
                'has_preview': thumbnailer.can_get_thumbnail(current_node.get_mimetype()),
                'mimetype': child.mimetype and child.mimetype.name,
                'size': child.size,
                'name': child.name,
            } for child in child_nodes]
        }

    @with_tempdir
    def test_list_nodes(self, temp_dir):
        """Ensure we can list our nodes."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        directory_1 = DirectoryFactory(data_library=data_library)
        library_url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        directory_url = reverse(
            'api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': f'/{directory_1.name}'})

        # list root
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), self.to_json_root(data_library))

        # list directory
        response = self.client.get(directory_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), self.to_json_node(directory_1))

        # directory does not exist
        data_library = DataLibraryFactory(owner=self.user)
        library_url_dne = reverse(
            'api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/dost-not-exists/'})

        response = self.client.get(library_url_dne)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

        # not our data library
        data_library2 = DataLibraryFactory()
        library_url2 = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library2.pk), 'path': '/'})

        response = self.client.get(library_url2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

        # anonymous get library
        self.client.logout()
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    @with_tempdir
    def test_list_file_node(self, temp_dir):
        """Ensure we can list files too."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        file = FileFactory(data_library=data_library)
        url = reverse('api_v1:lib-files', kwargs={'lib_id': str(data_library.pk), 'path': '/' + file.name})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertDictEqual(response.json(), self.to_json_node(current_node=file, child_nodes=[file]))

        # anonymous list node
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

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

        # anonymous rename
        self.client.logout()
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    @with_tempdir
    def test_mkdir(self, temp_dir):
        """Ensure we can create directories."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        url = reverse('api_v1:lib-mkdir', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        data = {'name': 'FooBar'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        directory = Node.objects.get(parent__isnull=True, data_library=data_library, name=data['name'])
        self.assertTrue(directory.pk)
        self.assertDictEqual(response.json(), {
            'file_type': Node.FileTypeChoices.DIRECTORY.value,
            'size': 0,
            'mimetype': None,
            'name': data['name'],
            'has_preview': False,
        })

        # nested mkdir
        nested_url = reverse('api_v1:lib-mkdir', kwargs={'lib_id': str(data_library.pk), 'path': f'/{data["name"]}'})
        response = self.client.post(nested_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        directory = Node.objects.get(parent__isnull=False, data_library=data_library, name=data['name'])
        self.assertTrue(directory.pk)
        self.assertDictEqual(response.json(), {
            'file_type': Node.FileTypeChoices.DIRECTORY.value,
            'size': 0,
            'mimetype': None,
            'name': data['name'],
            'has_preview': False,
        })

        # mkdir with the same name
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertListEqual(response.json(), [
            f'File "/{data["name"]}" already exists',
        ])

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

        # anonymous mkdir
        self.client.logout()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

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

        # anonymous rm
        self.client.logout()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    @with_tempdir
    def test_file_upload(self, temp_dir):
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        url = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        image = Image.new('RGB', (100, 100))

        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            image.save(temp_file)
            temp_file.seek(0)
            response = self.client.post(url, {'file': temp_file}, format='multipart')
            self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

            tmp_path = Path(temp_file.name)
            self.assertDictEqual(response.json(), {
                'name': tmp_path.name,
                'file_type': 'file',
                'mimetype': 'image/jpeg',
                'size': tmp_path.stat().st_size,
                'has_preview': True
            })

            # File already exists
            temp_file.seek(0)
            response = self.client.post(url, {'file': temp_file}, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            self.assertListEqual(response.json(), [
                f'File with name {Path(temp_file.name).name} already exists',
            ])

        # library does not exist
        url_lib_dne = reverse('api_v1:lib-upload', kwargs={'lib_id': str(uuid.uuid4()), 'path': '/'})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            image.save(temp_file)
            response = self.client.post(url_lib_dne, {'file': temp_file}, format='multipart')
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'DataLibrary matching query does not exist.'})

        # path does not exist
        url_path_dne = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': '/does-not-exist/'})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            image.save(temp_file)
            temp_file.seek(0)
            response = self.client.post(url_path_dne, {'file': temp_file}, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'Node matching query does not exist.'})

        # target path is not directory
        target_node = FileFactory(data_library=data_library)
        url_nad = reverse('api_v1:lib-upload', kwargs={'lib_id': str(data_library.pk), 'path': f'/{target_node.name}'})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            image.save(temp_file)
            temp_file.seek(0)
            response = self.client.post(url_nad, {'file': temp_file}, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
            self.assertDictEqual(response.json(), {'detail': 'Incorrect node type'})

        # anonymous file upload
        self.client.logout()
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            image.save(temp_file)
            temp_file.seek(0)
            response = self.client.post(url, {'file': temp_file}, format='multipart')
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code, response.data)

    @with_tempdir
    def test_file_download(self, temp_dir):
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
            temp_file.write(b'foobar')
            temp_file.seek(0)
            file_node = FileFactory(
                data_library=data_library,
                file=UploadedFile(temp_file),
                mimetype__name='text/plain',
            )

        url = reverse('api_v1:lib-download', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node.name}'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertEqual(response.headers['Content-Disposition'], f'inline; filename="{Path(temp_file.name).name}"')
        self.assertEqual(response.getvalue(), b'foobar')

        # download deleted file
        file_node_no_file = FileFactory(
            data_library=data_library,
            mimetype__name='text/plain',
        )
        no_file_url = reverse(
            'api_v1:lib-download', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node_no_file.name}'})
        response = self.client.get(no_file_url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json(), {'detail': 'A server error occurred.'})

        # Node does not exists
        url_dne = reverse('api_v1:lib-download', kwargs={'lib_id': str(data_library.pk), 'path': '/does-not-exist'})
        response = self.client.get(url_dne)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Root node
        url_dne = reverse('api_v1:lib-download', kwargs={'lib_id': str(data_library.pk), 'path': '/'})
        response = self.client.get(url_dne)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # anonymous file get
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AltNodeTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    @with_tempdir
    def test_image_thumbnail(self, temp_dir):
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            image = Image.new("RGB", size=(50, 50), color=(255, 0, 0))
            image.save(temp_file)
            temp_file.seek(0)
            file_node = ImageFactory(
                data_library=data_library,
                file=UploadedFile(temp_file),
                mimetype__name='image/jpeg',
            )

        url = '{}?v={}'.format(
            reverse('api_v1:lib-alt', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node.name}'}),
            '50x50',
        )
        response = self.client.get(url)
        self.assertTrue(AltNode.objects.filter(node=file_node).exists())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
        alt_node = AltNode.objects.filter(node=file_node).get()
        self.assertEqual(response.headers['Content-Disposition'], f'inline; filename="{Path(alt_node.file.name).name}"')
        self.assertTrue(len(response.getvalue()) > 100)

        # Invalid url -- no version
        url = reverse('api_v1:lib-alt', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node.name}'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': '?v= is required'})

        # Invalid url -- invalid version
        url = '{}?v={}'.format(
            reverse('api_v1:lib-alt', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node.name}'}),
            'test',
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # remove main file removes all thumbnails
        url = reverse('api_v1:lib-rm', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node.name}'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AltNode.objects.exists())
        self.assertFalse(Node.objects.exists())

    @with_tempdir
    def test_invalid_image(self, temp_dir):
        """Make thumbnail with invalid image data."""
        data_library = DataLibraryFactory(owner=self.user, data_source__options={'location': temp_dir})
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            temp_file.write(b'foobar')
            temp_file.seek(0)
            file_node = ImageFactory(
                data_library=data_library,
                file=UploadedFile(temp_file),
                mimetype__name='image/jpeg',
            )

        url = '{}?v={}'.format(
            reverse('api_v1:lib-alt', kwargs={'lib_id': str(data_library.pk), 'path': f'/{file_node.name}'}),
            '50x50',
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'detail': 'Can not open thumbnail'})
