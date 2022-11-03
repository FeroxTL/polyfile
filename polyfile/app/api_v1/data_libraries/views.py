# todo: make errors in one style maybe {"message": "error message"}
import re
import typing
from io import BytesIO
from uuid import UUID

from PIL import ImageOps, Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction, models
from django.db.models import Case, When
from django.http import Http404, FileResponse
from django.utils import timezone
from django.utils.http import http_date
from rest_framework import generics, permissions, exceptions, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from app.api_v1.data_libraries.serializers import data_library_serializers, node_serializers
from storage.models import DataLibrary, Node, AltNode, AbstractNode
from storage.utils import get_node_by_path, get_mimetype


class DataLibraryListCreateView(generics.ListCreateAPIView):
    """List of user's libraries."""
    serializer_class = data_library_serializers.DataLibrarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataLibrary.objects.filter(owner=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer: serializers.Serializer):
        data_library: DataLibrary = serializer.save(owner=self.request.user)
        provider = data_library.data_source.get_provider()
        provider.init_library(library=data_library)


class DataLibraryDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Details, updates and deletion of users library."""
    # todo add library  removal (support DELETE method) + remove all nested files in DataLibrary
    #  Maybe we should mark them as deleted, but physically delete all files (and lib) in periodic task
    #  In first version it COULD do rm -rf
    lookup_url_kwarg = 'lib_id'
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method.upper() in ['PUT', 'PATCH']:
            return data_library_serializers.DataLibraryUpdateSerializer
        return data_library_serializers.DataLibrarySerializer

    def get_queryset(self):
        return DataLibrary.objects.filter(owner=self.request.user)


class DataLibraryNodeListView(generics.RetrieveAPIView):
    """List of nodes in library."""
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'lib_id'
    serializer_class = data_library_serializers.DataLibrarySerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library: typing.Optional[DataLibrary] = None

    def get_object(self) -> typing.Optional[Node]:
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        self.library = get_object_or_404(queryset, **filter_kwargs)

        try:
            return get_node_by_path(library=self.library, path=path)
        except Node.DoesNotExist as e:
            raise Http404(str(e))

    @staticmethod
    def get_child_nodes(parent_node: Node) -> typing.Iterable[Node]:
        if parent_node.file_type == Node.FileTypeChoices.FILE:
            return [parent_node]
        else:
            return parent_node.get_children().select_related('mimetype').annotate(
                relevancy=Case(
                    When(file_type=Node.FileTypeChoices.DIRECTORY, then=2),
                    When(file_type=Node.FileTypeChoices.FILE, then=1),
                    output_field=models.IntegerField()
                )
            ).order_by('-relevancy', 'name')

    def retrieve(self, request, *args, **kwargs):
        current_node = self.get_object()
        if current_node is None:
            child_nodes = Node.objects.filter(parent__isnull=True, data_library=self.library)
        else:
            child_nodes = self.get_child_nodes(current_node)

        return Response({
            'library': data_library_serializers.DataLibrarySerializer(self.library).data,
            'current_node': node_serializers.NodeSerializer(current_node).data,
            'nodes': node_serializers.NodeSerializer(child_nodes, many=True).data,
        })


class DataLibraryNodeMoveView(generics.UpdateAPIView):
    """Move Node."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = node_serializers.NodeMoveSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library: typing.Optional[DataLibrary] = None

    def get_object(self):
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        self.library = get_object_or_404(queryset, **filter_kwargs)

        try:
            return get_node_by_path(library=self.library, path=path)
        except Node.DoesNotExist as e:
            raise Http404(str(e))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'library': self.library,
            'path': self.kwargs['path'],
        })
        return context

    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())


class DataLibraryNodeRenameView(generics.UpdateAPIView):
    """Rename Node."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = node_serializers.NodeRenameSerializer
    queryset = Node.objects.none()

    def get_object(self):
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        library = get_object_or_404(queryset, **filter_kwargs)

        try:
            node = get_node_by_path(library=library, path=path)
            if node is None:
                raise Node.DoesNotExist
            return node
        except Node.DoesNotExist as e:
            raise Http404(str(e))


class NodeUploadFileView(generics.CreateAPIView):
    """Upload file to library."""
    serializer_class = node_serializers.NodeCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'lib_id'

    def get_queryset(self):
        return DataLibrary.objects.filter(owner=self.request.user)

    def get_object(self) -> DataLibrary:
        try:
            lib_id = self.kwargs[self.lookup_url_kwarg]
            return self.get_queryset().get(id=lib_id)
        except DataLibrary.DoesNotExist as e:
            raise exceptions.NotFound(str(e))

    def get_serializer_context(self):
        library = self.get_object()
        context = super().get_serializer_context()
        context.update({
            'library': library,
            'path': self.kwargs['path'],
        })
        return context


class DataLibraryMkdirView(generics.CreateAPIView):
    """Create directory in library."""
    serializer_class = node_serializers.MkDirectorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Node.objects.none()
    lookup_url_kwarg = 'lib_id'

    def get_library(self, lib_id: UUID) -> DataLibrary:
        return DataLibrary.objects.get(owner=self.request.user, id=lib_id)

    def perform_create(self, serializer):
        library = self.get_library(self.kwargs[self.lookup_url_kwarg])
        serializer.save(library=library, owner=self.request.user, path=self.kwargs['path'])


class DataLibraryDeleteNodeView(generics.DestroyAPIView):
    """Remove file or directory (must be empty)."""
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'lib_id'
    queryset = Node.objects.none()

    def get_object(self):
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        library = get_object_or_404(queryset, **filter_kwargs)

        try:
            node = get_node_by_path(library=library, path=path)
            if node is None:
                raise Node.DoesNotExist

            if node.is_directory and node.get_children_count():
                raise exceptions.ParseError(
                    f'Can not remove "{node.name}": is not empty'
                )

            return node
        except Node.DoesNotExist as e:
            raise Http404(str(e))

    @transaction.atomic
    def perform_destroy(self, instance):
        # todo: maybe we should mark files as deleted and clean them later
        instance.file.delete()
        alt_nodes_queryset = instance.alt_nodes.all()
        for alt_node in alt_nodes_queryset:
            alt_node.file.delete()
        alt_nodes_queryset.delete()
        instance.delete()


class DataLibraryDownloadView(generics.RetrieveAPIView):
    lookup_url_kwarg = 'lib_id'
    permission_classes = [permissions.IsAuthenticated]
    queryset = Node.objects.none()

    def get_library(self, lib_id: UUID) -> DataLibrary:
        return DataLibrary.objects.get(owner=self.request.user, id=lib_id)

    def get_object(self):
        path = self.kwargs['path']

        try:
            library = self.get_library(self.kwargs[self.lookup_url_kwarg])
            instance = get_node_by_path(
                library=library,
                path=path,
                last_node_type=Node.FileTypeChoices.FILE,
                strict=True
            )
            return instance
        except (Node.DoesNotExist, DataLibrary.DoesNotExist) as e:
            raise exceptions.NotFound(str(e))

    def retrieve(self, request, *args, **kwargs):
        instance: AbstractNode = self.get_object()

        try:
            return FileResponse(
                instance.file.open('rb'),  # todo: use sendfile, that is really slow
                content_type=instance.get_mimetype(),
                headers={'Last-Modified': http_date(instance.updated_at.timestamp())}
            )
        except (ValueError, OSError):  # file.open failed
            raise exceptions.APIException()


class DataLibraryAltView(DataLibraryDownloadView):
    def _parse_thumb_size(self):
        size = self.request.query_params.get('v', '')
        match = re.match(r'^(\d+)x(\d+)$', size)
        if match:
            return tuple(map(int, match.groups()))

        raise exceptions.ParseError('?v= is invalid')

    def get_image_thumbnail(self, node) -> AltNode:
        thumb_size = self._parse_thumb_size()
        version = self.request.query_params.get('v')

        file_io = BytesIO()
        image = ImageOps.fit(Image.open(node.file), thumb_size, Image.ANTIALIAS)
        image.save(file_io, format='jpeg')

        mimetype = get_mimetype('image/jpeg')
        instance, created = AltNode.objects.get_or_create(
            version=version,
            node=node,
            defaults=dict(
                mimetype=mimetype,
                data_library_id=node.data_library_id,
                file=InMemoryUploadedFile(
                    file=file_io,
                    field_name=None,
                    name=f'{version}.{node.name}',  # todo: field length
                    content_type=mimetype.name,
                    size=file_io.tell(),
                    charset=None,
                ),
            ),
        )
        return instance

    def get_object(self):
        node = super().get_object()
        version = self.request.query_params.get('v')
        if version is None:
            raise exceptions.NotFound('?v= is required')

        try:
            return AltNode.objects.get(node=node, version=version)
        except AltNode.DoesNotExist:
            # todo: if mimetype.startswith('image/') ...
            #  or move to thumbnailer
            return self.get_image_thumbnail(node=node)
