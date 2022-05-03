import io
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.forms import forms, fields
from minio import Minio, S3Error
from urllib3.exceptions import RequestError

from app.utils.models import get_field
from storage.data_providers.base import BaseProvider
from storage.data_providers.exceptions import ProviderException
from storage.models import DataLibrary, DataSourceOption


class MinioStorage:
    def __init__(self, client_options: dict):
        self.client = Minio(**client_options)

    def bucket_exists(self, bucket_name) -> bool:
        return self.client.bucket_exists(bucket_name)

    def make_bucket(self, bucket_name):
        return self.client.make_bucket(bucket_name)

    def upload(self, bucket_name: str, path: str, file: UploadedFile):
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=str(Path(path) / file.name),
            data=file,
            length=file.size,
        )

    def get_object(self, bucket_name: str, path: str) -> File:
        resp = self.client.get_object(bucket_name=bucket_name, object_name=path)
        return File(file=io.BytesIO(resp.read()), name=Path(path).name)

    def remove(self, bucket_name: str, path: str):
        """Remove object or directory."""
        # remove_object is always success even if path does not exist
        self.client.remove_object(bucket_name=bucket_name, object_name=path)

    def move(self, bucket_name: str, source_path: str, target_path: str):
        """
        Move file or directory into target path.

        S3 does not have "MOVE" action, so we download files one by one into temp file and place them into target path.
        """
        source_path = source_path.lstrip('/')
        target_path = target_path.lstrip('/')
        if source_path.endswith('/') and not target_path.endswith('/'):
            target_path += '/'

        for item in self.client.list_objects(bucket_name=bucket_name, prefix=source_path, recursive=True):
            with NamedTemporaryFile() as f:
                self.client.fget_object(bucket_name=bucket_name, object_name=item.object_name, file_path=f.name)
                self.client.remove_object(bucket_name=bucket_name, object_name=item.object_name)
                item_target = str(item.object_name).replace(source_path, target_path, 1)
                self.client.fput_object(bucket_name=bucket_name, object_name=item_target, file_path=f.name)


class MinioValidationForm(forms.Form):
    endpoint = fields.CharField(
        label='Endpoint',
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length
    )
    access_key = fields.CharField(
        label='Access key',
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length
    )
    secret_key = fields.CharField(
        label='Secret key',
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length
    )
    secure = fields.BooleanField(
        label='Secure',
        required=False,
    )


class MinioStorageProvider(BaseProvider):
    provider_id = 'MinioStorage'
    verbose_name = 'Minio Storage'
    validation_class = MinioValidationForm

    def __init__(self, library: DataLibrary, options: dict):
        super().__init__(library=library, options=options)
        self.storage = MinioStorage(client_options=self.transform_options(options))

    @classmethod
    def validate_options(cls, options: dict):
        options = super().validate_options(options=options)
        storage = MinioStorage(client_options=options)
        try:
            storage.client.list_buckets()
        except (S3Error, RequestError) as e:
            raise ValidationError({'endpoint': str(e)})

    def init_library(self):
        bucket_name = self.get_user_bucket()
        if not self.storage.bucket_exists(bucket_name):
            self.storage.make_bucket(bucket_name=bucket_name)

    def get_user_bucket(self) -> str:
        return str(self.library.pk)

    def upload_file(self, path: str, uploaded_file: UploadedFile):
        path = path.lstrip('/')
        self.storage.upload(bucket_name=self.get_user_bucket(), path=path, file=uploaded_file)

    def open_file(self, path: str) -> File:
        if not path or path == '/':
            raise ProviderException('Suspicious operation')

        return self.storage.get_object(
            bucket_name=self.get_user_bucket(),
            path=path,
        )

    def mkdir(self, target_path: str):
        """S3 does not have file-system like directories, so let's not create them."""
        pass

    def rm(self, path: str):
        if not path:
            raise ProviderException('Suspicious operation')

        self.storage.remove(bucket_name=self.get_user_bucket(), path=path)

    def rename(self, path: str, name: str):
        if not path or not name:
            raise ProviderException('Suspicious operation')

        bucket_name = self.get_user_bucket()
        target_path = str(Path(path).parent / name)

        self.storage.move(bucket_name=bucket_name, source_path=path, target_path=target_path)
