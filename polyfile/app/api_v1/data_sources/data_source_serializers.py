from rest_framework import serializers

from app.utils.models import get_field
from storage.base_data_provider import provider_registry
from storage.models import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    """DataSource serializer for creates/listings."""
    data_provider_id = serializers.ChoiceField(
        label=get_field(DataSource, 'data_provider_id').verbose_name,
        choices=[],  # filled in __init__
    )

    class Meta:
        model = DataSource
        fields = [
            'id',
            'name',
            'data_provider_id',
            'options',
        ]
        read_only_fields = [
            'id',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_provider_id'].choices = [
            (p.provider_id, p.verbose_name)
            for p in provider_registry.providers
        ]

    def validate_options(self, attrs):
        data_provider_id = self.initial_data.get('data_provider_id')

        if data_provider_id and provider_registry.has_provider(data_provider_id):
            provider_cls = provider_registry.get_provider(data_provider_id)
            provider_cls.transform_options(options=attrs)
        return attrs


class DataSourceUpdateSerializer(DataSourceSerializer):
    """DataSource serializer for updates."""
    data_provider_id = serializers.ReadOnlyField(
        label=get_field(DataSource, 'data_provider_id').verbose_name,
    )

    def validate_options(self, attrs):
        data_provider_id = self.instance.data_provider_id
        provider_cls = provider_registry.get_provider(data_provider_id)
        provider_cls.transform_options(options=attrs)
        return attrs
