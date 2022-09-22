from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage, Storage
from django.forms import forms, fields

from app.utils.models import get_field
from storage.data_providers.base import BaseProvider
from storage.models import DataSourceOption


class FileStorageForm(forms.Form):
    root_directory = fields.CharField(
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length,
        label='Root directory',
        help_text='Root directory on server. Must exist',
    )

    def clean(self):
        root_directory = self.cleaned_data.get('root_directory', None)
        if root_directory is not None:
            root_directory = Path(root_directory)
            if not root_directory.exists() or not root_directory.is_dir():
                raise ValidationError({'root_directory': f'"{root_directory}" is not directory or does not exist'})
        return self.cleaned_data


class FileSystemStorageProvider(BaseProvider):
    provider_id = 'FileStorage'
    verbose_name = 'Disk File Storage'
    validation_class = FileStorageForm

    def get_storage(self) -> Storage:
        assert 'root_directory' in self.options
        root_directory = Path(self.options['root_directory'])
        return FileSystemStorage(location=root_directory)
