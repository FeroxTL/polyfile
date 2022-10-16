from django.apps import AppConfig

from storage.base_data_provider import provider_registry


class SystemFileStorageConfig(AppConfig):
    name = 'contrib.storages.filesystem_storage'

    def ready(self):
        from contrib.storages.filesystem_storage.provider import FileSystemStorageProvider
        provider_registry.register(FileSystemStorageProvider)
