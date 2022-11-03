import typing
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django_cte import CTEManager

from storage.base_data_provider import BaseProvider, provider_registry
from storage.fields import DynamicStorageFileField


def get_data_provider_class(data_provider_id) -> typing.Type[BaseProvider]:
    return provider_registry.get_provider(data_provider_id)


class DataSource(models.Model):
    """
    Credentials and settings, that applies to DataProvider.

    Only admins can set up this.
    """
    id = models.BigAutoField(primary_key=True)
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
    id = models.BigAutoField(primary_key=True)
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


class AbstractNode(models.Model):
    file = DynamicStorageFileField(
        upload_to=DynamicStorageFileField.default_upload_to,  # required for django migrations
        blank=True,
    )
    data_library = models.ForeignKey(
        DataLibrary,
        verbose_name='Data library',
        on_delete=models.PROTECT,
    )
    mimetype = models.ForeignKey(
        Mimetype,
        verbose_name='Mimetype',
        on_delete=models.PROTECT,
        blank=True, null=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='Date update',
        auto_now=True,
    )

    class Meta:
        abstract = True

    DoesNotExist: typing.Type[ObjectDoesNotExist]
    data_library_id: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._path = None

    @property
    def path(self):
        assert self._path is not None, (
            f'No "path" attribute was provided using annotations '
            f'({self.__class__.__name__}.objects.annotate(...)) or direct assignments.'
        )
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def url(self):
        raise NotImplementedError

    def get_mimetype(self) -> str:
        if self.mimetype is not None:
            return self.mimetype.name
        return 'application/octet-stream'

    def is_node_cls(self):
        return isinstance(self, Node)


class Node(AbstractNode):
    """File or directory."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
        db_index=True,
        blank=False, null=False,
    )

    size = models.PositiveIntegerField(
        verbose_name='Size',
        default=0,
        help_text='Size in bytes',
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

    parent = models.ForeignKey(
        'self',
        related_name='children_set',
        null=True, db_index=True,
        on_delete=models.PROTECT,
    )

    created_at = models.DateTimeField(
        verbose_name='Creation date',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'
        unique_together = [
            ('name', 'parent', 'data_library'),
        ]

    get_file_type_display: typing.Callable
    objects = models.Manager()
    cte_objects = CTEManager()

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.get_file_type_display()} ({self.name or "<root>"})>'
    __repr__ = __str__

    @property
    def is_directory(self) -> bool:
        return self.file_type == self.FileTypeChoices.DIRECTORY

    def get_children(self):
        return Node.objects.filter(parent=self)

    def get_children_count(self):
        # todo: really strange thing
        return self.get_children().count()

    @property
    def url(self):
        return reverse(
            'api_v1:lib-download',
            kwargs={'lib_id': str(self.data_library_id), 'path': '/' + self.path}
        )


class AltNode(AbstractNode):
    """Alternative version of Node."""
    id = models.BigAutoField(primary_key=True)
    node = models.ForeignKey(
        Node,
        related_name='alt_nodes',
        null=False, blank=False,
        on_delete=models.PROTECT,
    )
    version = models.CharField(
        verbose_name='Version',
        max_length=255,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Alt Node'
        verbose_name_plural = 'Alt Nodes'
        unique_together = [
            ('node', 'version'),
        ]
        ordering = ['-id']

    objects = models.Manager()
    DoesNotExist: ObjectDoesNotExist

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.version}>'
    __repr__ = __str__

    @property
    def url(self):
        url = reverse(
            'api_v1:lib-alt',
            kwargs={'lib_id': str(self.data_library_id), 'path': '/' + self.path}
        )
        url += '?' + urlencode({'v': self.version})
        return url
