from django.apps import AppConfig

from storage.base_data_provider import provider_registry


class MinioStorageConfig(AppConfig):
    name = 'contrib.storages.s3_storage'

    def ready(self):
        from contrib.storages.s3_storage.provider import S3StorageProvider
        provider_registry.register(S3StorageProvider)
