from django.apps import AppConfig
from django.conf import settings


class StorageConfig(AppConfig):
    name = 'polyfile.storage'

    def ready(self):  # noqa
        from polyfile.storage.thumbnailer import thumbnailer

        if settings.NORMAL_RUNNING:
            thumbnailer.setup()
