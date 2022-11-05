from django.apps import AppConfig


class StorageConfig(AppConfig):
    name = 'storage'

    def ready(self):
        from storage.thumbnailer import thumbnailer

        thumbnailer.setup()
