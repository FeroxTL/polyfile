from rest_framework import generics, permissions

from app.api_v1.data_sources import data_source_serializers
from storage.models import DataSource


class DataSourceListCreateView(generics.ListCreateAPIView):
    """List/create data sources."""
    serializer_class = data_source_serializers.DataSourceSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DataSource.objects.all()


class DataSourceListUpdateView(generics.RetrieveUpdateAPIView):
    """Data source get/update."""
    serializer_class = data_source_serializers.DataSourceUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DataSource.objects.all()
