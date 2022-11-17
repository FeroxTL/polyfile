from django.apps import AppConfig
from django.conf import settings


class StorageConfig(AppConfig):
    name = 'storage'

    def ready(self):  # noqa
        from storage.thumbnailer import thumbnailer

        if settings.NORMAL_RUNNING:
            thumbnailer.setup()
