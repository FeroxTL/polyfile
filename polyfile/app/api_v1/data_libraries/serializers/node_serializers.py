import mimetypes
from operator import itemgetter

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from rest_framework import serializers, exceptions

from app.utils.models import get_field

from storage.models import Node
from storage.thumbnailer import thumbnailer
from storage.utils import get_node_by_path, adapt_path, get_mimetype


class NodeSerializer(serializers.ModelSerializer):
    mimetype = serializers.ReadOnlyField(source='mimetype_id', default=None)
    has_preview = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = [
            'name',
            'file_type',
            'mimetype',
            'size',
            'has_preview',
        ]
        read_only_fields = [
            'name',
            'file_type',
            'size',
        ]

    @staticmethod
    def get_has_preview(instance: Node):
        return thumbnailer.can_get_thumbnail(mimetype=instance.mimetype_id)


class NodeCreateSerializer(NodeSerializer):
    file = serializers.FileField(write_only=True)

    class Meta(NodeSerializer.Meta):
        fields = [
            'file',
        ] + NodeSerializer.Meta.fields

    def create(self, validated_data: dict):
        file: UploadedFile = validated_data['file']
        library, path = itemgetter('library', 'path')(self.context)

        try:
            parent_node = get_node_by_path(
                library=library,
                path=path,
                last_node_type=Node.FileTypeChoices.DIRECTORY,
            )
        except Node.DoesNotExist as e:
            # todo one style for all errors
            raise exceptions.ValidationError({'detail': str(e)})

        content_type, _ = mimetypes.guess_type(str(file))
        node, created = Node.objects.get_or_create(
            name=file.name,
            parent=parent_node,
            data_library=library,
            defaults=dict(
                file_type=Node.FileTypeChoices.FILE,
                size=file.size,
                mimetype=get_mimetype(content_type),
                file=file,
            ),
        )

        if not created:
            raise exceptions.ValidationError(f'File with name {node.name} already exists', code='unique')

        return node


class NodeMoveSerializer(serializers.ModelSerializer):
    target_path = serializers.CharField(required=True, allow_null=False, allow_blank=False, write_only=True)

    class Meta:
        model = Node
        fields = [
            'target_path',
            'name',
            'file_type',
            'created_at',
            'updated_at',
            'size',
        ]
        read_only_fields = [
            'id',
            'name',
            'file_type',
            'created_at',
            'updated_at',
            'size',
        ]

    @transaction.atomic
    def update(self, instance: Node, validated_data):
        # todo
        library, source_path = itemgetter('library', 'path')(self.context)
        target_path = validated_data['target_path']
        # data_provider = get_data_provider(data_source=library.data_source)
        # super().update(instance, validated_data)

        try:
            source_node = get_node_by_path(library=library, path=source_path)
            target_directory = get_node_by_path(
                library=library,
                path=target_path,
                last_node_type=Node.FileTypeChoices.DIRECTORY
            )
        except Node.DoesNotExist as e:
            raise exceptions.ValidationError({'path': str(e)})

        print('source:', source_node)
        print('source parent:', source_node.get_parent())
        print('target:', target_directory)

        assert target_directory != source_node.get_parent()

        source_node.move(target_directory, pos='sorted-child')

        # try:
        #     data_provider.move(
        #         library=library,
        #         source_path=path,
        #         target_directory=target_directory,
        #     )
        # except ProviderException as e:
        #     raise exceptions.ValidationError(e)

        return self.instance


class NodeRenameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            'name',
            'file_type',
            'created_at',
            'updated_at',
            'size',
        ]
        read_only_fields = [
            'id',
            'file_type',
            'created_at',
            'updated_at',
            'size',
        ]


class MkDirectorySerializer(NodeSerializer):
    """Create directory node in library."""
    name = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        max_length=get_field(Node, 'name').max_length,
        label=get_field(Node, 'name').verbose_name,
        # todo: should add regexp to check name?
    )

    @staticmethod
    def validate_name(name: str):
        if name in ['.', '..'] or '/' in name:
            raise exceptions.ValidationError('This name is invalid')
        return name

    @transaction.atomic
    def create(self, validated_data):
        library, path, name = itemgetter('library', 'path', 'name')(validated_data)
        params = dict(
            name=name,
            file_type=Node.FileTypeChoices.DIRECTORY,
            data_library=library,
        )

        try:
            parent_node = get_node_by_path(library=library, path=path)
        except Node.DoesNotExist as e:
            raise exceptions.ParseError(str(e))

        node, created = Node.objects.get_or_create(parent=parent_node, **params)
        if not created:
            raise exceptions.ValidationError(f'File "{adapt_path(path)}/{name}" already exists')
            # todo: one style exceptions

        return node
