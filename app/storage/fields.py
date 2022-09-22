from django.core.files.storage import Storage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.urls import reverse


def _get_storage(node_instance) -> Storage:
    provider = node_instance.data_library.data_source.get_provider(node=node_instance)
    return provider.storage


class DynamicStorageFieldFile(FieldFile):
    def __init__(self, instance, field, name):
        super().__init__(instance, field, name)
        self.storage = _get_storage(instance)

    def url(self):
        return reverse(
            'api_v1:lib-download',
            kwargs={'lib_id': str(self.instance.data_library_id), 'path': '/' + self.instance.path}
        )


class DynamicStorageFileField(models.FileField):
    attr_class = DynamicStorageFieldFile

    @staticmethod
    def default_upload_to(instance, filename):
        provider = instance.data_library.data_source.get_provider(node=instance)

        return provider.get_upload_to(instance=instance, filename=filename)

    def pre_save(self, model_instance, add):
        storage = _get_storage(model_instance)

        self.storage = storage
        model_instance.file.storage = storage

        return super().pre_save(model_instance, add)

    def deconstruct(self):
        """Get rid of some fields in django migrations."""
        name, path, args, kwargs = super().deconstruct()
        for field_name in ('storage', 'upload_to'):
            kwargs.pop(field_name, None)
        return name, path, args, kwargs
