from django.apps import AppConfig


class StorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storage'

    def ready(self):
        from storage.data_providers.base import provider_register
        from storage.data_providers.file_storage import FileSystemStorageProvider
        provider_register.register(FileSystemStorageProvider)
