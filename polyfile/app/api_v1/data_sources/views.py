from rest_framework import generics, permissions

from polyfile.app.api_v1.data_sources import data_source_serializers
from polyfile.app.api_v1.utils.metadata import V1Metadata
from polyfile.storage.models import DataSource


class DataSourceListCreateView(generics.ListCreateAPIView):
    """List/create data sources."""
    name = 'Data source list'
    serializer_class = data_source_serializers.DataSourceSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DataSource.objects.all()
    metadata_class = V1Metadata


class DataSourceDetailView(generics.RetrieveUpdateAPIView):
    """Data source get/update."""
    name = 'Data source detail'
    serializer_class = data_source_serializers.DataSourceUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DataSource.objects.all()
    metadata_class = V1Metadata
