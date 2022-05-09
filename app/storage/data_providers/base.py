import typing

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.forms import forms

from storage.models import DataLibrary


class BaseProvider:
    validation_class: forms.Form = forms.Form

    @property
    def provider_id(self) -> str:
        raise NotImplementedError

    @property
    def verbose_name(self) -> str:
        raise NotImplementedError

    def __init__(self, library: DataLibrary, options: dict):
        super().__init__()
        self.library = library
        self.options = options

    def __str__(self):
        return self.verbose_name

    def init_provider(self):
        pass

    def init_library(self):
        pass

    @classmethod
    def transform_options(cls, options: dict):
        """Transform options from k:v of strings to required types."""
        form = cls.validation_class(data=options)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return form.cleaned_data

    @classmethod
    def validate_options(cls, options: dict):
        return cls.transform_options(options)

    def upload_file(self, path: str, uploaded_file: UploadedFile):
        raise NotImplementedError

    def open_file(self, path: str) -> File:
        raise NotImplementedError

    def mkdir(self, target_path: str):
        raise NotImplementedError

    def rm(self, path: str):
        raise NotImplementedError

    def rename(self, path: str, name: str):
        raise NotImplementedError


class ProviderRegister:
    TypeBaseProvider = typing.Type[BaseProvider]

    def __init__(self):
        self._registry = {}

    def has_provider(self, provider_id: str):
        return provider_id in self._registry

    def register(self, provider: TypeBaseProvider):
        self._registry[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> TypeBaseProvider:
        return self._registry[provider_id]

    @property
    def providers(self) -> typing.Iterable[TypeBaseProvider]:
        return self._registry.values()


provider_registry = ProviderRegister()
