from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from storage.data_providers.exceptions import ProviderException
from storage.data_providers.file_storage import FileSystemStorageProvider
from storage.data_providers.utils import get_data_provider
from storage.factories import DirectoryFactory, DataLibraryFactory, FileFactory, DataSourceFactory
from storage.models import Node
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
        node = get_node_by_path(data_library.root_dir, root_path)
        self.assertEqual(node, data_library.root_dir)

        # relative root
        node = get_node_by_path(data_library.root_dir, '')
        self.assertEqual(node, data_library.root_dir)

        # directory
        node = get_node_by_path(data_library.root_dir, directory_path)
        self.assertEqual(node, directory)

        # relative directory
        node = get_node_by_path(data_library.root_dir, directory_path[1:])
        self.assertEqual(node, directory)

        # file
        node = get_node_by_path(data_library.root_dir, file_path)
        self.assertEqual(node, file)

        # relative file
        node = get_node_by_path(data_library.root_dir, file_path[1:])
        self.assertEqual(node, file)

        # does not exist
        with self.assertRaises(Node.DoesNotExist):
            get_node_by_path(data_library.root_dir, '/does-not-exist/')


class FileSystemStorageProviderTests(TestCase):
    """FileStorage tests."""
    def test_init_storage(self):
        with TemporaryDirectory() as f:
            data_source = DataSourceFactory(
                data_provider_id=FileSystemStorageProvider.provider_id,
                options={'root_directory': f},
            )

            provider = get_data_provider(data_source=data_source)
            provider.init_provider()

            self.assertTrue(isinstance(provider, FileSystemStorageProvider))
            self.assertEqual(provider.provider_id, FileSystemStorageProvider.provider_id)
            self.assertTrue((Path(f) / 'data').exists())

            # users library
            library = DataLibraryFactory()
            provider.init_library(library=library)
            self.assertTrue((Path(f) / 'data' / str(library.pk) / 'files').exists())

    def test_mkdir(self):
        """Ensure we can make directories in storage."""
        with TemporaryDirectory() as f:
            provider = FileSystemStorageProvider(options={'root_directory': f})
            provider.init_provider()
            dir_name = 'FooBar'
            library = DataLibraryFactory()
            provider.init_library(library)

            # mkdir
            realpath = provider.mkdir(library=library, path='/', name=dir_name)
            self.assertEqual(realpath, Path(f) / 'data' / str(library.pk) / 'files' / dir_name)
            self.assertTrue(realpath.exists())

            # suspicious mkdir
            with self.assertRaises(ProviderException) as e:
                provider.mkdir(library=library, path='/', name='../foobar/')
            self.assertEqual(str(e.exception), 'Suspicious operation')

            # relative path
            dir_name2 = 'FooBar2'
            realpath = provider.mkdir(library=library, path=dir_name, name=dir_name2)
            self.assertEqual(realpath, Path(f) / 'data' / str(library.pk) / 'files' / dir_name / dir_name2)
            self.assertTrue(realpath.exists())

            # directory already exists
            with self.assertRaises(ProviderException) as e:
                provider.mkdir(library=library, path=dir_name, name=dir_name2)
            self.assertEqual(str(e.exception), 'directory already exists')

    def test_rm(self):
        """Ensure we can remove nodes in storage."""
        with TemporaryDirectory() as f:
            provider = FileSystemStorageProvider(options={'root_directory': f})
            provider.init_provider()
            dir_name = 'FooBar'
            library = DataLibraryFactory()
            provider.init_library(library)
            root_path = Path(f) / 'data' / str(library.pk) / 'files'

            # rmdir
            realpath = root_path / dir_name
            realpath.mkdir()
            provider.rm(library=library, path=f'/{dir_name}/')
            self.assertFalse(realpath.exists())

            # rmdir relative path
            realpath = root_path / dir_name
            realpath.mkdir()
            provider.rm(library=library, path=f'{dir_name}/')
            self.assertFalse(realpath.exists())

            # rm file
            realpath = root_path / dir_name
            realpath.touch()
            provider.rm(library=library, path=f'{dir_name}/')
            self.assertFalse(realpath.exists())

            # rmdir root directory
            with self.assertRaises(ProviderException):
                provider.rm(library=library, path='/')
            with self.assertRaises(ProviderException):
                provider.rm(library=library, path='')

            # rm directory that does not exist
            with self.assertRaises(ProviderException):
                provider.rm(library=library, path='/does-not-exist/')

    def test_rename(self):
        """Ensure we can rename files/directories in storage."""
        with TemporaryDirectory() as f:
            provider = FileSystemStorageProvider(options={'root_directory': f})
            provider.init_provider()
            dir_name = 'FooBar'
            library = DataLibraryFactory()
            provider.init_library(library)
            root_path = Path(f) / 'data' / str(library.pk) / 'files'

            # rename directory
            realpath = root_path / dir_name
            realpath.mkdir()
            new_dir_name = 'BarBaz'
            provider.rename(library=library, path=f'/{dir_name}/', name=new_dir_name)
            self.assertFalse(realpath.exists())
            realpath = root_path / new_dir_name
            self.assertTrue(realpath.exists())
            realpath.rmdir()

            # rename root directory
            with self.assertRaises(ProviderException):
                provider.rename(library=library, path='/', name=new_dir_name)

            with self.assertRaises(ProviderException):
                provider.rename(library=library, path='/../', name=new_dir_name)

            # Rename relative path
            realpath = root_path / dir_name
            realpath.mkdir()
            new_dir_name = 'BarBaz'
            provider.rename(library=library, path=f'{dir_name}/', name=new_dir_name)
            self.assertFalse(realpath.exists())
            realpath = root_path / new_dir_name
            self.assertTrue(realpath.exists())
            realpath.rmdir()
