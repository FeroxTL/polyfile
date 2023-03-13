from django.apps import AppConfig

from polyfile.storage.base_data_provider import provider_registry


class SystemFileStorageConfig(AppConfig):
    name = 'polyfile.contrib.storages.filesystem_storage'

    def ready(self):
        from polyfile.contrib.storages.filesystem_storage.provider import FileSystemStorageProvider
        provider_registry.register(FileSystemStorageProvider)
