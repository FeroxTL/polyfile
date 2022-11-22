import mimetypes
from operator import itemgetter

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import serializers, exceptions

from app.utils.models import get_field

from storage.models import Node
from storage.thumbnailer import thumbnailer
from storage.utils import get_node_by_path, get_mimetype, adapt_path


class NodeSerializer(serializers.ModelSerializer):
    """Default Node serializer."""
    mimetype = serializers.ReadOnlyField(source='mimetype_id', default=None)
    has_preview = serializers.SerializerMethodField(method_name='_get_has_preview')

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
            'mimetype',
            'file_type',
            'size',
        ]

    @staticmethod
    def _get_has_preview(instance: Node):
        return thumbnailer.can_get_thumbnail(mimetype=instance.mimetype_id)


class NodeCreateSerializer(NodeSerializer):
    """Create node serializer."""
    file = serializers.FileField(write_only=True)

    class Meta(NodeSerializer.Meta):
        fields = [
            'file',
        ] + NodeSerializer.Meta.fields
        read_only_fields = NodeSerializer.Meta.read_only_fields + ['name']

    def create(self, validated_data: dict):
        """Validate data and create node."""
        file: UploadedFile = validated_data['file']
        library, path = itemgetter('library', 'path')(self.context)

        try:
            parent_node = get_node_by_path(
                library=library,
                path=path,
                last_node_type=Node.FileTypeChoices.DIRECTORY,
            )
        except Node.DoesNotExist as e:
            raise exceptions.ValidationError(e)

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
            raise exceptions.ValidationError(
                f'{node.get_file_type_display()} "{node.name}" already exists',
                code='unique'
            )

        return node


class NodeMoveSerializer(serializers.ModelSerializer):
    """Move Node serializer."""
    target_path = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=True,
        write_only=True
    )

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

    def update(self, instance: Node, validated_data):
        """Move file or directory to target location."""
        source_node = instance
        library, source_path = itemgetter('library', 'path')(self.context)
        source_path = adapt_path(source_path)
        target_path = adapt_path(validated_data['target_path'])

        if source_node.is_directory and target_path.startswith(source_path):
            raise exceptions.ValidationError(f'Can not move {source_node.name} to a subdirectory of itself')

        try:
            target_directory = get_node_by_path(
                library=library,
                path=target_path,
                last_node_type=Node.FileTypeChoices.DIRECTORY
            )
        except Node.DoesNotExist as e:
            raise exceptions.ValidationError(e)

        try:
            source_node.parent = target_directory
            source_node.updated_at = timezone.now()
            with transaction.atomic():
                source_node.save(update_fields=['parent', 'updated_at'])
        except IntegrityError:
            raise exceptions.ValidationError(
                f'Can not move {source_node.name}: {source_node.get_file_type_display()} already exists'
            )

        return source_node


class NodeRenameSerializer(NodeSerializer):
    """Rename node serializer."""
    name = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        max_length=get_field(Node, 'name').max_length,
        label=get_field(Node, 'name').verbose_name,
        # todo: should add regexp to check name?
    )

    @staticmethod
    def validate_name(name: str):
        """Ensure name is valid."""
        if name in ['.', '..'] or '/' in name:
            raise exceptions.ValidationError('This name is invalid')
        return name


class MkDirectorySerializer(NodeRenameSerializer):
    """Create directory node in library."""
    @transaction.atomic
    def create(self, validated_data):
        """Validate data and create instance."""
        library, path, name = itemgetter('library', 'path', 'name')(validated_data)

        try:
            parent_node = get_node_by_path(library=library, path=path)
        except Node.DoesNotExist as e:
            raise exceptions.ParseError(str(e))

        node, created = Node.objects.get_or_create(
            parent=parent_node,
            name=name,
            file_type=Node.FileTypeChoices.DIRECTORY,
            data_library=library,
        )
        if not created:
            raise exceptions.ValidationError(
                f'{node.get_file_type_display()} "{node.name}" already exists',
                code='unique'
            )

        return node
