from rest_framework import serializers
from rest_framework.metadata import SimpleMetadata


class V1Metadata(SimpleMetadata):
    """Metadata for api v1."""
    def get_serializer_info(self, serializer):
        """Given an instance of a serializer, return a list of metadata about its fields."""
        if hasattr(serializer, 'child'):
            serializer = serializer.child
        return [
            {'attribute': field_name, **self.get_field_info(field)}
            for field_name, field in serializer.fields.items()
            if not isinstance(field, serializers.HiddenField)
        ]
