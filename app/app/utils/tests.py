from pathlib import Path

from django.core.files.storage import Storage
from django.core.files.uploadedfile import UploadedFile
from rest_framework.fields import DateTimeField

from storage.data_providers.base import BaseProvider, provider_registry


def drf_dt(dt) -> str:
    return DateTimeField().to_representation(dt)


class TestProvider(BaseProvider):
    provider_id = 'test_provider'
    verbose_name = 'Test provider'

    def get_storage(self) -> Storage:
        pass

    def list_files(self, path: str):
        pass

    def upload_file(self, path: str, uploaded_file: UploadedFile):
        pass

    def open_file(self, path: str) -> Path:
        pass

    def mkdir(self, path: str, name: str):
        pass

    def rm(self, path: str):
        pass

    def rename(self, path: str, name: str):
        pass


provider_registry.register(TestProvider)
