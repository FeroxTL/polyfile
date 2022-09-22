from django.apps import AppConfig

from storage.data_providers.base import provider_registry


class StorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storage'

    def ready(self):
        from storage.data_providers.file_storage import FileSystemStorageProvider
        from storage.data_providers.minio_storage import S3StorageProvider
        provider_registry.register(FileSystemStorageProvider)
        provider_registry.register(S3StorageProvider)
