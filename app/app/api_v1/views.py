# todo: make errors in one style maybe {"message": "error message"}
import mimetypes
import typing
from pathlib import Path
from uuid import UUID

from django.db import transaction, models
from django.db.models import Case, When
from django.http import FileResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import http_date
from rest_framework import permissions, generics, exceptions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.data_providers.exceptions import ProviderException
from storage.data_providers.utils import get_data_provider
from storage.models import DataLibrary, Node
from storage.utils import remove_node, get_node_by_path
from . import serializers as v1_serializers


class ApiItemList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request):
        # todo: use this for global menu? add permissions? or enable only in debug mode?
        return Response([
            {'url': reverse('api_v1:lib-list')},
        ])


class DataLibraryListCreateView(generics.ListCreateAPIView):
    """List of user's libraries."""
    serializer_class = v1_serializers.DataLibrarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DataLibrary.objects.filter(owner=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        root_dir = Node.add_root(name='', file_type=Node.FileTypeChoices.DIRECTORY)
        serializer.save(owner=self.request.user, root_dir=root_dir)
        provider = get_data_provider(serializer.instance.data_source)
        provider.init_library(library=serializer.instance)


class DataLibraryDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Details, updates and deletion of users library."""
    # todo add library  removal (support DELETE method) + remove all nested files in DataLibrary
    #  Maybe we should mark them as deleted, but physically delete all files (and lib) in periodic task
    #  In first version it COULD do rm -rf
    lookup_url_kwarg = 'lib_id'
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method.upper() in ['PUT', 'PATCH']:
            return v1_serializers.DataLibraryInstanceSerializer
        return v1_serializers.DataLibrarySerializer

    def get_queryset(self):
        return DataLibrary.objects.filter(owner=self.request.user)


class DataLibraryNodeListView(generics.RetrieveAPIView):
    """List of nodes in library."""
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'lib_id'
    # todo: serializer_class for openApi
    serializer_class = v1_serializers.DataLibrarySerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library: typing.Optional[DataLibrary] = None

    def get_object(self) -> Node:
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        self.library = get_object_or_404(queryset, **filter_kwargs)

        try:
            return get_node_by_path(root_node=self.library.root_dir, path=path)
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
        child_nodes = self.get_child_nodes(current_node)

        return Response({
            'library': v1_serializers.DataLibrarySerializer(self.library).data,
            'current_node': v1_serializers.NodeSerializer(current_node).data,
            'nodes': v1_serializers.ChildNodeSerializer(child_nodes, many=True).data,
        })


class DataLibraryNodeMoveView(generics.UpdateAPIView):
    """Move Node."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = v1_serializers.NodeMoveSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library: typing.Optional[DataLibrary] = None

    def get_object(self):
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        self.library = get_object_or_404(queryset, **filter_kwargs)

        try:
            return get_node_by_path(root_node=self.library.root_dir, path=path)
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
    serializer_class = v1_serializers.NodeRenameSerializer
    queryset = Node.objects.none()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library: typing.Optional[DataLibrary] = None

    def get_object(self):
        path = self.kwargs['path']
        queryset = DataLibrary.objects.filter(owner=self.request.user)
        filter_kwargs = {self.lookup_field: self.kwargs['lib_id']}
        self.library = get_object_or_404(queryset, **filter_kwargs)

        try:
            return get_node_by_path(root_node=self.library.root_dir, path=path)
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


class NodeUploadFileView(generics.CreateAPIView):
    """Upload file to library."""
    serializer_class = v1_serializers.NodeSerializer
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
    serializer_class = v1_serializers.RepoDirectorySerializer
    lookup_url_kwarg = 'lib_id'

    def get_queryset(self):
        return DataLibrary.objects.filter(owner=self.request.user)

    def get_library(self, lib_id: UUID) -> DataLibrary:
        return DataLibrary.objects.get(owner=self.request.user, id=lib_id)

    def perform_create(self, serializer):
        library = self.get_library(self.kwargs[self.lookup_url_kwarg])
        serializer.save(library=library, owner=self.request.user, path=self.kwargs['path'])


class DataLibraryRmFileView(generics.DestroyAPIView):
    """Remove file or directory (must be empty)."""
    serializer_class = v1_serializers.NodeSerializer
    lookup_url_kwarg = 'lib_id'
    queryset = Node.objects.none()

    def get_library(self, lib_id: UUID) -> DataLibrary:
        return DataLibrary.objects.get(owner=self.request.user, id=lib_id)

    def destroy(self, request, *args, **kwargs):
        path = self.kwargs['path']

        try:
            library = self.get_library(self.kwargs[self.lookup_url_kwarg])
            remove_node(library=library, path=path)
        except (Node.DoesNotExist, DataLibrary.DoesNotExist) as e:
            raise exceptions.NotFound(str(e))
        except ProviderException as e:
            raise exceptions.ParseError(str(e))

        return Response(status=status.HTTP_204_NO_CONTENT)


class DataLibraryDownloadView(generics.RetrieveAPIView):
    lookup_url_kwarg = 'lib_id'
    queryset = Node.objects.none()

    def get_library(self, lib_id: UUID) -> DataLibrary:
        return DataLibrary.objects.get(owner=self.request.user, id=lib_id)

    def retrieve(self, request, *args, **kwargs):
        path = self.kwargs['path']

        try:
            library = self.get_library(self.kwargs[self.lookup_url_kwarg])
            provider = get_data_provider(library.data_source)
            fullpath: Path = provider.download_file(library=library, path=path)
            stat_obj = fullpath.stat()
        except (Node.DoesNotExist, DataLibrary.DoesNotExist) as e:
            raise exceptions.NotFound(str(e))
        except ProviderException as e:
            raise exceptions.ParseError(str(e))

        # todo: content_type = current_node.mime_type.name
        # print(http_date(stat_obj.st_mtime), stat_obj.st_mtime)
        # print(http_date(current_node.updated_at.timestamp()))

        content_type, encoding = mimetypes.guess_type(str(fullpath))
        content_type = content_type or 'application/octet-stream'
        response = FileResponse(fullpath.open('rb'), content_type=content_type)

        response.headers["Last-Modified"] = http_date(stat_obj.st_mtime)
        if encoding:
            response.headers["Content-Encoding"] = encoding
        return response
