from pathlib import Path

from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile

from storage.data_providers.base import BaseProvider
from storage.data_providers.exceptions import ProviderException
from storage.models import DataLibrary


class FileSystemStorageProvider(BaseProvider):
    provider_id = 'FileStorage'
    verbose_name = 'Disk File Storage'

    def __init__(self, library: DataLibrary, options: dict):
        self.root_directory = Path(options['root_directory'])
        super().__init__(library=library, options=options)

    @property
    def data_directory(self) -> Path:
        return self.root_directory / 'data'

    @property
    def tmp_directory(self) -> Path:
        return self.root_directory / 'tmp'

    def init_provider(self):
        self.root_directory.mkdir(exist_ok=True)
        self.tmp_directory.mkdir(exist_ok=True)
        self.data_directory.mkdir(exist_ok=True)

    def init_library(self):
        storage = self.get_user_storage()
        Path(storage.path('')).mkdir(parents=True, exist_ok=True)

    def _get_relative_user_data_directory(self) -> Path:
        return Path('data') / str(self.library.pk) / 'files'

    def get_user_storage(self):
        """Storage with root in user directory."""
        return FileSystemStorage(location=self.root_directory / self._get_relative_user_data_directory())

    def list_files(self, path: str):
        # todo -- what for?
        storage = self.get_user_storage()
        return storage.listdir(path)

    def upload_file(self, path: str, uploaded_file: UploadedFile):
        if path and path[0] == '/':
            path = path[1:]

        storage = self.get_user_storage()
        path_name = Path(path) / uploaded_file.name

        if storage.exists(path_name):
            raise ProviderException('file already exists')

        return storage.save(path_name, content=uploaded_file)

    def open_file(self, path: str) -> File:
        if path and path[0] == '/':
            path = path[1:]

        if not path:
            raise ProviderException('Suspicious operation')

        storage = self.get_user_storage()
        return storage.open(path)

    def mkdir(self, path: str, name: str):
        # todo: remove 'name' argument
        if path and path[0] == '/':
            path = path[1:]

        storage = self.get_user_storage()
        path_name = Path(path) / name
        real_path = Path(storage.path(path_name))

        if real_path.exists():
            raise ProviderException('directory already exists')

        real_path.mkdir()
        return real_path

    def rm(self, path: str):
        if path and path[0] == '/':
            path = path[1:]

        if not path:
            raise ProviderException('Suspicious operation')

        storage = self.get_user_storage()
        storage.delete(path)

    def rename(self, path: str, name: str):
        if path and path[0] == '/':
            path = path[1:]

        if not path or not name:
            raise ProviderException('Suspicious operation')

        storage = self.get_user_storage()
        real_path = Path(storage.path(path))
        new_path = Path(storage.path(real_path.parent / name))

        if new_path.parent != real_path.parent:
            raise ProviderException('Suspicious operation')

        if storage.exists(new_path):
            raise ProviderException('Suspicious operation')

        real_path.rename(new_path)
