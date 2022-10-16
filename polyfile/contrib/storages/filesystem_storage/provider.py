from pathlib import Path

from django.core.files.storage import Storage, FileSystemStorage

from storage.base_data_provider import BaseProvider
from contrib.storages.filesystem_storage.forms import FileStorageForm


class FileSystemStorageProvider(BaseProvider):
    provider_id = 'FileStorage'
    verbose_name = 'Disk File Storage'
    validation_class = FileStorageForm

    def get_storage(self) -> Storage:
        assert 'root_directory' in self.options
        root_directory = Path(self.options['root_directory'])
        return FileSystemStorage(location=root_directory)
