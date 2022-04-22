import os
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile

from storage.data_providers.base import BaseProvider
from storage.data_providers.exceptions import ProviderException
from storage.models import DataLibrary


class FileSystemStorageProvider(BaseProvider):
    provider_id = 'FileStorage'
    verbose_name = 'Disk File Storage'

    def __init__(self, options: dict):
        super().__init__(options=options)
        self.root_directory = Path(options['root_directory'])

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

    def init_library(self, library: DataLibrary):
        self.get_user_root_directory(library=library).mkdir(exist_ok=True)
        self.get_user_data_dir(library=library).mkdir(exist_ok=True)

    def get_user_root_directory(self, library: DataLibrary):
        return self.data_directory / Path(str(library.pk))

    def get_user_data_dir(self, library: DataLibrary):
        return self.get_user_root_directory(library=library) / 'files'

    def list_files(self, library: DataLibrary, path: str):
        user_dir = self.get_user_data_dir(library=library)
        real_path = (user_dir / Path(path)).resolve()

        if not real_path.is_relative_to(user_dir):
            raise ProviderException('Suspicious operation')

        try:
            return list(real_path.iterdir())
        except FileNotFoundError:
            raise ProviderException('File does not exist')

    def upload_file(self, library: DataLibrary, path: str, uploaded_file: UploadedFile):
        if path and path[0] == '/':
            path = path[1:]

        user_dir = self.get_user_data_dir(library=library)
        real_path = (user_dir / Path(path) / Path(uploaded_file.name)).resolve()

        if not real_path.is_relative_to(user_dir):
            raise ProviderException('Suspicious operation')

        if real_path.exists():
            raise ProviderException('file already exists')

        real_path.write_bytes(uploaded_file.file.read())
        return path

    def download_file(self, library: DataLibrary, path: str) -> Path:
        if path and path[0] == '/':
            path = path[1:]

        user_dir = self.get_user_data_dir(library=library)
        real_path = (user_dir / Path(path)).resolve()

        if not real_path.is_relative_to(user_dir):
            raise ProviderException('Suspicious operation')

        return real_path

    def mkdir(self, library: DataLibrary, path: str, name: str):
        if path and path[0] == '/':
            path = path[1:]

        user_dir = self.get_user_data_dir(library=library)
        real_path = (user_dir / Path(path) / Path(name)).resolve()

        if not real_path.is_relative_to(user_dir):
            raise ProviderException('Suspicious operation')

        if real_path.exists():
            raise ProviderException('directory already exists')

        real_path.mkdir()
        return real_path

    def rm(self, library: DataLibrary, path: str):
        if path and path[0] == '/':
            path = path[1:]

        user_dir = self.get_user_data_dir(library=library)
        real_path = (user_dir / Path(path)).resolve()

        if not real_path.is_relative_to(user_dir) or user_dir == real_path:
            raise ProviderException('Suspicious operation')

        try:
            if real_path.is_file():
                os.remove(real_path)
            else:
                os.rmdir(real_path)
        except FileNotFoundError:
            # todo: more logging
            raise ProviderException('No such file or directory')

    def rename(self, library: DataLibrary, path: str, name: str):
        if path and path[0] == '/':
            path = path[1:]

        user_dir = self.get_user_data_dir(library=library)
        real_path = (user_dir / Path(path)).resolve()
        new_path = real_path.parent / name

        if not real_path.is_relative_to(user_dir) or user_dir == real_path or new_path.exists():
            raise ProviderException('Suspicious operation')

        real_path.replace(new_path)
