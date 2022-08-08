import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.core.exceptions import SuspiciousFileOperation, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.factories import SuperuserFactory
from app.utils.tests import TestProvider
from storage.data_providers.exceptions import ProviderException
from storage.data_providers.file_storage import FileSystemStorageProvider
from storage.data_providers.utils import get_data_provider
from storage.factories import DirectoryFactory, DataLibraryFactory, FileFactory, DataSourceFactory
from storage.models import Node, DataSource
from storage.utils import get_node_by_path


class StorageTests(TestCase):
    def test_get_node_by_path(self):
        """Test getting node by its path."""
        data_library = DataLibraryFactory()
        root_path = '/'
        directory = DirectoryFactory(parent=data_library.root_dir)
        directory_path = f'/{directory.name}/'
        file = FileFactory(parent=directory)
        file_path = f'{directory_path}{file.name}'

        # root
        node = get_node_by_path(data_library.root_dir_id, root_path)
        self.assertEqual(node, data_library.root_dir)

        # relative root
        node = get_node_by_path(data_library.root_dir_id, '')
        self.assertEqual(node, data_library.root_dir)

        # directory
        node = get_node_by_path(data_library.root_dir_id, directory_path)
        self.assertEqual(node, directory)

        # relative directory
        node = get_node_by_path(data_library.root_dir_id, directory_path[1:])
        self.assertEqual(node, directory)

        # file
        node = get_node_by_path(data_library.root_dir_id, file_path)
        self.assertEqual(node, file)

        # relative file
        node = get_node_by_path(data_library.root_dir_id, file_path[1:])
        self.assertEqual(node, file)

        # does not exist
        with self.assertRaises(Node.DoesNotExist):
            get_node_by_path(data_library.root_dir_id, '/does-not-exist/')


class FileSystemStorageProviderTests(TestCase):
    """FileStorage tests."""
    def test_init_storage(self):
        with TemporaryDirectory() as f:
            data_source = DataSourceFactory(
                data_provider_id=FileSystemStorageProvider.provider_id,
                options={'root_directory': f},
            )
            library = DataLibraryFactory(data_source=data_source)

            provider = get_data_provider(library=library)
            provider.init_provider()

            self.assertTrue(isinstance(provider, FileSystemStorageProvider))
            self.assertEqual(provider.provider_id, FileSystemStorageProvider.provider_id)
            self.assertTrue((Path(f) / 'data').exists())

            # users library
            provider.init_library()
            self.assertTrue((Path(f) / 'data' / str(library.pk) / 'files').exists())

    def test_invalid_options(self):
        """Ensure FileSystemStorageProvider correctly validates its options."""
        with TemporaryDirectory() as f:
            data_source = DataSourceFactory(
                data_provider_id=FileSystemStorageProvider.provider_id,
                options={'root_directory': f},
            )
            library = DataLibraryFactory(data_source=data_source)
            not_existent_path = Path(f) / 'does-not-exist'

            provider = get_data_provider(library=library)
            provider.validate_options(data_source.options_dict)

            # directory does not exist
            with self.assertRaises(ValidationError) as e:
                provider.validate_options({'root_directory': not_existent_path})

            self.assertDictEqual(e.exception.message_dict, {
                'root_directory': [f'"{not_existent_path}" is not directory or does not exist']
            })

            # directory is not provided
            with self.assertRaises(ValidationError) as e:
                provider.validate_options({})

            self.assertDictEqual(e.exception.message_dict, {
                'root_directory': ['This field is required.']
            })

    def test_file_upload(self):
        """Ensure we can upload files to storage."""
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file, TemporaryDirectory() as f:
            tmp_file.write(b'foobar')
            provider = FileSystemStorageProvider(library=DataLibraryFactory(), options={'root_directory': f})
            provider.init_provider()
            provider.init_library()

            name = provider.upload_file(path='/', uploaded_file=UploadedFile(tmp_file))
            self.assertEqual(name, Path(tmp_file.name).name)
            filepath = Path(f, 'data', str(provider.library.pk), 'files', name)
            self.assertTrue(filepath.exists())
            self.assertEqual(filepath.read_bytes(), b'foobar')

            # upload with same name
            with self.assertRaises(ProviderException):
                provider.upload_file(path='/', uploaded_file=UploadedFile(tmp_file))

    def test_mkdir(self):
        """Ensure we can make directories in storage."""
        with TemporaryDirectory() as f:
            provider = FileSystemStorageProvider(library=DataLibraryFactory(), options={'root_directory': f})
            provider.init_provider()
            dir_name = 'FooBar'
            provider.init_library()

            # mkdir
            realpath = provider.mkdir(target_path=f'/{dir_name}')
            self.assertEqual(realpath, Path(f) / 'data' / str(provider.library.pk) / 'files' / dir_name)
            self.assertTrue(realpath.exists())

            # suspicious mkdir
            with self.assertRaises(SuspiciousFileOperation):
                provider.mkdir(target_path='/../foobar/')

            # relative path
            dir_name2 = 'FooBar2'
            realpath = provider.mkdir(target_path=f'{dir_name}/{dir_name2}')
            self.assertEqual(realpath, Path(f) / 'data' / str(provider.library.pk) / 'files' / dir_name / dir_name2)
            self.assertTrue(realpath.exists())

            # directory already exists
            with self.assertRaises(ProviderException) as e:
                provider.mkdir(target_path=f'{dir_name}/{dir_name2}')
            self.assertEqual(str(e.exception), 'directory already exists')

    def test_rm(self):
        """Ensure we can remove nodes in storage."""
        with TemporaryDirectory() as f:
            provider = FileSystemStorageProvider(library=DataLibraryFactory(), options={'root_directory': f})
            provider.init_provider()
            dir_name = 'FooBar'
            provider.init_library()
            root_path = Path(f) / 'data' / str(provider.library.pk) / 'files'

            # rmdir
            realpath = root_path / dir_name
            realpath.mkdir()
            provider.rm(path=f'/{dir_name}/')
            self.assertFalse(realpath.exists())

            # rmdir relative path
            realpath = root_path / dir_name
            realpath.mkdir()
            provider.rm(path=f'{dir_name}/')
            self.assertFalse(realpath.exists())

            # rm file
            realpath = root_path / dir_name
            realpath.touch()
            provider.rm(path=f'{dir_name}/')
            self.assertFalse(realpath.exists())

            # rmdir root directory
            with self.assertRaises(ProviderException):
                provider.rm(path='/')
            with self.assertRaises(ProviderException):
                provider.rm(path='')

            # rm directory that does not exist (that is ok)
            provider.rm(path='/does-not-exist/')

    def test_rename(self):
        """Ensure we can rename files/directories in storage."""
        with TemporaryDirectory() as f:
            provider = FileSystemStorageProvider(library=DataLibraryFactory(), options={'root_directory': f})
            provider.init_provider()
            dir_name = 'FooBar'
            provider.init_library()
            root_path = Path(f) / 'data' / str(provider.library.pk) / 'files'

            # rename directory
            realpath = root_path / dir_name
            realpath.mkdir()
            new_dir_name = 'BarBaz'
            provider.rename(path=f'/{dir_name}/', name=new_dir_name)
            self.assertFalse(realpath.exists())
            realpath = root_path / new_dir_name
            self.assertTrue(realpath.exists())
            realpath.rmdir()

            # rename root directory
            with self.assertRaises(SuspiciousFileOperation):
                provider.rename(path='/', name=new_dir_name)

            with self.assertRaises(SuspiciousFileOperation):
                provider.rename(path='/../', name=new_dir_name)

            # Rename relative path
            realpath = root_path / dir_name
            realpath.mkdir()
            new_dir_name = 'BarBaz'
            provider.rename(path=f'{dir_name}/', name=new_dir_name)
            self.assertFalse(realpath.exists())
            realpath = root_path / new_dir_name
            self.assertTrue(realpath.exists())
            realpath.rmdir()

            # rename, but already exists
            realpath = root_path / dir_name
            realpath.mkdir()
            new_path = root_path / 'BarBaz'
            new_path.mkdir()
            with self.assertRaises(SuspiciousFileOperation):
                provider.rename(path=str(dir_name), name=new_path.name)

            realpath.rmdir()
            new_path.rmdir()

            # Rename to something strange
            realpath = root_path / dir_name
            realpath.mkdir()
            foo_dir = root_path / 'foo'
            foo_dir.mkdir()

            new_dir_name = 'foo/BarBaz'

            with self.assertRaises(SuspiciousFileOperation):
                provider.rename(path=str(dir_name), name=new_dir_name)


class DataSourceAdminTest(TestCase):
    def setUp(self) -> None:
        self.user = SuperuserFactory()
        self.client.force_login(self.user)

    @staticmethod
    def get_options(options: dict, delete_list_keys: list = None):
        result_options = {}
        delete_list_keys = delete_list_keys or []

        for i, key in enumerate(options.keys()):
            result_options[f'options-{i}-key'] = key
            result_options[f'options-{i}-value'] = options[key]
            if key in delete_list_keys:
                result_options[f'options-{i}-DELETE'] = 1

        result = {
            'options-TOTAL_FORMS': len(options),
            'options-INITIAL_FORMS': 0,
            'options-MIN_NUM_FORMS': 0,
            'id_options-MAX_NUM_FORMS': 1000,
            **result_options
        }
        return result

    def test_datasource_create(self):
        """Ensure we can create DataSource."""
        url = reverse('admin:storage_datasource_add')
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({
                'foo': 'bar',
                'bar': 'baz',
                '': '',
            }, delete_list_keys=['bar']),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DataSource.objects.count(), 1)
        data_source = DataSource.objects.get()
        self.assertEqual(data_source.name, 'FooBar')
        self.assertEqual(data_source.data_provider_id, TestProvider.provider_id)
        self.assertDictEqual(data_source.options_dict, {'foo': 'bar'})

        url = reverse('admin:storage_datasource_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_datasource_update(self):
        """Ensure we can update DataSource."""
        datasource = DataSourceFactory()
        url = reverse('admin:storage_datasource_change', args=[datasource.pk])
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({}),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DataSource.objects.count(), 1)
        data_source = DataSource.objects.get()
        self.assertEqual(data_source.name, 'FooBar')

    def test_datasource_options_invalid(self):
        """Errors while creating DataSource."""
        url = reverse('admin:storage_datasource_add')
        data = {
            'name': '',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({
                'foo': 'bar',
            }),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform']
        self.assertTrue('name' in form.errors)

        # valid data, invalid options ("foo" value is blank)
        data = {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({'foo': ''}),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 1)
        form = formset.forms[0]
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('value' in form.errors)

        # invalid value in options
        data = {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({'foo': 'bar'}),
        }
        with mock.patch.object(TestProvider, 'validate_options') as p:
            p.side_effect = ValidationError({'foo': 'foo is invalid'})
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        form = response.context['adminform']
        self.assertEqual(len(form.errors), 0)
        self.assertEqual(len(response.context['inline_admin_formsets']), 1)
        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 1)
        self.assertListEqual(formset.non_form_errors(), ['foo: foo is invalid'])


class DataLibraryAdminTest(TestCase):
    def setUp(self) -> None:
        self.user = SuperuserFactory()
        self.client.force_login(self.user)

    def test_init_library(self):
        """Ensure we can create DataLibrary and init them."""
        url = reverse('admin:storage_datalibrary_add')
        root_directory = DirectoryFactory(name='')

        with mock.patch.object(TestProvider, 'init_library') as init_library:
            data_source = DataSourceFactory(
                data_provider_id=TestProvider.provider_id,
                options={},
            )
            data = {
                'name': 'Test',
                'owner': self.user.pk,
                'data_source': data_source.pk,
                'root_dir': root_directory.pk,
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)
            init_library.assert_called()

        url = reverse('admin:storage_datalibrary_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change_library(self):
        """Ensure DataLibrary is not reinitialized on update."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('admin:storage_datalibrary_change', args=[str(data_library.pk)])

        with mock.patch.object(TestProvider, 'init_library') as init_library:
            data = {
                'name': 'Test',
                'owner': data_library.owner.pk,
                'data_source': data_library.data_source.pk,
                'root_dir': data_library.root_dir.pk,
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)
            init_library.assert_not_called()
