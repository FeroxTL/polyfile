import typing
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile

from storage.models import DataLibrary


class BaseProvider:
    @property
    def provider_id(self) -> str:
        raise NotImplementedError

    @property
    def verbose_name(self) -> str:
        raise NotImplementedError

    def __str__(self):
        return self.verbose_name

    def __init__(self, options: dict):
        self.options = options

    def init_provider(self):
        pass

    def init_library(self, library: DataLibrary):
        pass

    def list_files(self, library: DataLibrary, path: str):
        raise NotImplementedError

    def upload_file(self, library: DataLibrary, path: str, uploaded_file: UploadedFile):
        raise NotImplementedError

    def download_file(self, library: DataLibrary, path: str) -> Path:
        # Todo: pathlib.Path is only for test purposes. We should use more abstract object, but
        #  api methods in storages were not stabilized yet.
        raise NotImplementedError

    def mkdir(self, library: DataLibrary, path: str, name: str):
        raise NotImplementedError

    def rm(self, library: DataLibrary, path: str):
        raise NotImplementedError

    def rename(self, library: DataLibrary, path: str, name: str):
        raise NotImplementedError


class ProviderRegister:
    TypeBaseProvider = typing.Type[BaseProvider]

    def __init__(self):
        self._registry = {}

    def register(self, provider: TypeBaseProvider):
        self._registry[provider.provider_id] = provider

    def get_provider(self, provider_id) -> TypeBaseProvider:
        return self._registry[provider_id]

    @property
    def providers(self) -> typing.Iterable[TypeBaseProvider]:
        return self._registry.values()


provider_register = ProviderRegister()
