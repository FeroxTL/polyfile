from pathlib import Path

from django.core.files.uploadedfile import UploadedFile
from rest_framework.fields import DateTimeField

from storage.data_providers.base import BaseProvider, provider_register
from storage.models import DataLibrary


def drf_dt(dt) -> str:
    return DateTimeField().to_representation(dt)


class TestProvider(BaseProvider):
    provider_id = 'test_provider'
    verbose_name = 'Test provider'

    def list_files(self, library: DataLibrary, path: str):
        pass

    def upload_file(self, library: DataLibrary, path: str, uploaded_file: UploadedFile):
        pass

    def download_file(self, library: DataLibrary, path: str) -> Path:
        pass

    def mkdir(self, library: DataLibrary, path: str, name: str):
        pass

    def rm(self, library: DataLibrary, path: str):
        pass

    def rename(self, library: DataLibrary, path: str, name: str):
        pass


provider_register.register(TestProvider)
