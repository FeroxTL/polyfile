from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile
from django.forms import forms, fields

from app.utils.models import get_field
from storage.data_providers.base import BaseProvider
from storage.data_providers.exceptions import ProviderException
from storage.models import DataLibrary, DataSourceOption


class FileStorageForm(forms.Form):
    root_directory = fields.CharField(
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length,
    )

    def clean(self):
        root_directory = self.cleaned_data.get('root_directory', None)
        if root_directory is not None:
            root_directory = Path(root_directory)
            if not root_directory.exists() or not root_directory.is_dir():
                raise ValidationError({'root_directory': f'"{root_directory}" is not directory or does not exist'})
        return self.cleaned_data


class FileSystemStorageProvider(BaseProvider):
    provider_id = 'FileStorage'
    verbose_name = 'Disk File Storage'
    validation_class = FileStorageForm

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

    @staticmethod
    def _path_to_rel_path(path: str) -> str:
        return path.lstrip('/')

    def get_user_storage(self) -> FileSystemStorage:
        """Storage with location root in user directory."""
        return FileSystemStorage(location=self.root_directory / self._get_relative_user_data_directory())

    def upload_file(self, path: str, uploaded_file: UploadedFile) -> str:
        path = self._path_to_rel_path(path)
        storage = self.get_user_storage()
        path_name = Path(path) / uploaded_file.name

        if storage.exists(path_name):
            raise ProviderException('file already exists')

        return storage.save(path_name, content=uploaded_file)

    def open_file(self, path: str) -> File:
        path = self._path_to_rel_path(path)

        if not path:
            raise ProviderException('Suspicious operation')

        storage = self.get_user_storage()
        return storage.open(path)

    def mkdir(self, target_path: str):
        relative_path = self._path_to_rel_path(target_path)
        storage = self.get_user_storage()
        real_path = Path(storage.path(relative_path))

        if real_path.exists():
            raise ProviderException('directory already exists')

        real_path.mkdir()
        return real_path

    def rm(self, path: str):
        path = self._path_to_rel_path(path)

        if not path:
            raise ProviderException('Suspicious operation')

        storage = self.get_user_storage()
        storage.delete(path)

    def rename(self, path: str, name: str):
        path = self._path_to_rel_path(path)

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
