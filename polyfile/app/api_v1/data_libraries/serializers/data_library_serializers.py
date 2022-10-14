from rest_framework import serializers

from storage.models import DataLibrary


class DataLibrarySerializer(serializers.ModelSerializer):
    """DataLibrary serializer for creates/listings."""
    class Meta:
        model = DataLibrary
        fields = [
            'id',
            'name',
            'data_source',
        ]
        read_only_fields = [
            'id',
        ]


class DataLibraryUpdateSerializer(DataLibrarySerializer):
    """DataLibrary serializer for updates."""
    class Meta(DataLibrarySerializer.Meta):
        read_only_fields = DataLibrarySerializer.Meta.read_only_fields + [
            'data_source',
        ]
