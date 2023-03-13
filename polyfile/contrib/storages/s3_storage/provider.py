from django.core.files.storage import Storage
from django.utils.timezone import now
from storages.backends.s3boto3 import S3StaticStorage, S3Boto3Storage

from polyfile.contrib.storages.s3_storage.forms import S3ValidationForm
from polyfile.storage.base_data_provider import BaseProvider
from polyfile.storage.models import DataLibrary, AbstractNode


class S3StorageProvider(BaseProvider):
    """Provider to S3 storages."""
    provider_id = 'MinioStorage'
    verbose_name = 'Minio Storage'
    validation_class = S3ValidationForm
    storage: S3Boto3Storage

    def get_storage(self) -> Storage:
        """Get instance of Storage."""
        options = self.transform_options(self.options)
        if self.node is not None:
            options['bucket_name'] = self._get_user_bucket_name(self.node.data_library_id)
        return S3StaticStorage(**options)

    def _is_bucket_exists(self, name: str) -> bool:
        """Check if bucket exists."""
        bucket = self.storage.connection.Bucket(name)
        return bucket.creation_date is not None

    def init_library(self, library: DataLibrary):
        """Initialize DataLibrary."""
        bucket_name = self._get_user_bucket_name(library.pk)

        if not self._is_bucket_exists(bucket_name):
            self.storage.connection.create_bucket(Bucket=bucket_name)

    @staticmethod
    def _get_user_bucket_name(library_id: int) -> str:
        return str(library_id)

    @staticmethod
    def get_upload_to(instance: AbstractNode, filename: str) -> str:
        """Target upload path."""
        path = []
        if not instance.is_node_cls():
            path.append('alt')
        path.extend([now().strftime('%Y.%m'), filename])
        return '/'.join(path)
