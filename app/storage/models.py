import typing
import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from treebeard.mp_tree import MP_Node


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
    root_dir = models.ForeignKey(
        'storage.Node',
        verbose_name='Root directory',
        limit_choices_to={'depth': 1},
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


class Node(MP_Node):
    """File or directory."""
    name = models.CharField(
        verbose_name='Name',
        max_length=255,
        db_index=True,
        blank=True, null=False,
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
    mimetype = models.ForeignKey(
        Mimetype,
        verbose_name='Mimetype',
        on_delete=models.PROTECT,
        blank=True, null=True,
    )

    # auto_now_add=True is incompatible with MP_Node
    created_at = models.DateTimeField(
        verbose_name='Created',
        default=timezone.now,
    )
    updated_at = models.DateTimeField(
        verbose_name='Updated',
        default=timezone.now,
    )

    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'

    node_order_by = ['name', 'file_type']
    get_file_type_display: typing.Callable
    DoesNotExist: typing.Type[ObjectDoesNotExist]

    def __str__(self):
        return '{}: {}'.format(self.get_file_type_display(), self.name or '<root>')

    @property
    def is_directory(self):
        return self.file_type == self.FileTypeChoices.DIRECTORY
