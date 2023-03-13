from django.apps import AppConfig

from polyfile.storage.base_data_provider import provider_registry


class MinioStorageConfig(AppConfig):
    name = 'polyfile.contrib.storages.s3_storage'

    def ready(self):
        from polyfile.contrib.storages.s3_storage.provider import S3StorageProvider
        provider_registry.register(S3StorageProvider)
