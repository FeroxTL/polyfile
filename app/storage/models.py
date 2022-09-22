import typing
import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_cte import CTEManager

from storage.data_providers.base import BaseProvider
from storage.data_providers.utils import get_data_provider_class
from storage.fields import DynamicStorageFileField


class DataSource(models.Model):
    """
    Credentials and settings, that applies to DataProvider.

    Only admins can set up this.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        verbose_name='Data source name',
        max_length=255,
        blank=False, null=False,
    )
    data_provider_id = models.CharField(
        max_length=255,
        verbose_name='Data provider',
    )

    class Meta:
        verbose_name = 'Data source'
        verbose_name_plural = 'Data sources'

    objects = models.Manager()
    options: models.QuerySet

    def __str__(self):
        return self.name or '<empty name>'

    @property
    def options_dict(self) -> dict:
        return dict(self.options.values_list('key', 'value'))

    def get_provider(self, node: typing.Optional['Node'] = None) -> BaseProvider:
        provider_class = get_data_provider_class(self.data_provider_id)
        return provider_class(options=self.options_dict, node=node)


class DataSourceOption(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=512)
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='options',
        blank=False, null=False,
    )

    objects = models.Manager()

    def __str__(self):
        return f'{self.key}: {self.value}'


class DataLibrary(models.Model):
    """Endpoint, that connects user to DataSource."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    name = models.CharField(
        max_length=255,
        blank=False,
        null=False
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    data_source = models.ForeignKey(
        DataSource,
        verbose_name='Data source',
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = 'Data library'
        verbose_name_plural = 'Data libraries'

    objects = models.Manager()
    DoesNotExist: ObjectDoesNotExist

    def __str__(self):
        return self.name


class Mimetype(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        verbose_name='Mimetype',
        max_length=256,
    )

    class Meta:
        verbose_name = 'Mime type'
        verbose_name_plural = 'Mime types'

    objects = models.Manager()

    def __str__(self):
        return self.name


class Node(models.Model):
    """File or directory."""
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
        db_index=True,
        blank=True, null=False,
    )
    file = DynamicStorageFileField(
        upload_to=DynamicStorageFileField.default_upload_to,  # required for django migrations
        blank=True,
    )
    size = models.PositiveIntegerField(
        verbose_name='Size',
        default=0,
        help_text='Size in bytes',
    )
    data_library = models.ForeignKey(
        DataLibrary,
        verbose_name='Data library',
        on_delete=models.PROTECT,
    )

    class FileTypeChoices(models.TextChoices):
        DIRECTORY = 'directory', 'Directory'
        FILE = 'file', 'File'

    file_type = models.CharField(
        verbose_name='Node type',
        max_length=16,
        db_index=True,
        choices=FileTypeChoices.choices,
    )
    mimetype = models.ForeignKey(
        Mimetype,
        verbose_name='Mimetype',
        on_delete=models.PROTECT,
        blank=True, null=True,
    )

    parent = models.ForeignKey(
        'self',
        related_name='children_set',
        null=True, db_index=True,
        on_delete=models.PROTECT,
    )

    created_at = models.DateTimeField(
        verbose_name='Created',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='Updated',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'
        unique_together = [
            ('name', 'parent', 'data_library'),
        ]

    data_library_id: int
    get_file_type_display: typing.Callable
    DoesNotExist: typing.Type[ObjectDoesNotExist]
    objects = models.Manager()
    cte_objects = CTEManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._path = None

    def __str__(self):
        return '{}: {}'.format(self.get_file_type_display(), self.name or '<root>')

    @property
    def is_directory(self):
        return self.file_type == self.FileTypeChoices.DIRECTORY

    @classmethod
    def add_root(cls, **kwargs):
        return cls.objects.create(parent=None, **kwargs)

    def add_child(self, **kwargs):
        return Node.objects.create(parent=self, **kwargs)

    def get_children(self):
        return Node.objects.filter(parent=self)

    def get_children_count(self):
        return self.get_children().count()

    @property
    def path(self):
        assert self._path is not None, \
            'No path was provided using annotations (Node.objects.annotate(...)) or direct assignments.'
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
