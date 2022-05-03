from django.db import transaction
from rest_framework import serializers

from app.utils.models import get_field
from storage.data_providers.base import provider_registry
from storage.models import DataSource, DataSourceOption


class DataSourceOptionSerializer(serializers.ModelSerializer):
    """Data source option serializer."""
    class Meta:
        model = DataSourceOption
        fields = [
            'key',
            'value',
        ]


class DataSourceOptionsListSerializer(serializers.ListSerializer):
    """Data source options update."""
    child = DataSourceOptionSerializer()

    def validate(self, attrs):
        if self.parent.instance is not None:
            data_provider_id = self.parent.instance.data_provider_id
        else:
            data_provider_id = self.parent.initial_data.get('data_provider_id')

        assert data_provider_id is not None

        options = {option['key']: option['value'] for option in attrs}
        provider_cls = provider_registry.get_provider(data_provider_id)
        provider_cls.validate_options(options=options)
        return attrs

    def update(self, instance: DataSource, validated_data: list):
        with transaction.atomic():
            data_sources = [
                DataSourceOption(key=option['key'], value=option['value'], data_source=instance)
                for option in validated_data
            ]
            instance.options.all().delete()
            DataSourceOption.objects.bulk_create(data_sources)

    def create(self, validated_data):
        data_sources = [
            DataSourceOption(key=option['key'], value=option['value'], data_source=self.parent.instance)
            for option in validated_data
        ]
        DataSourceOption.objects.bulk_create(data_sources)


class DataSourceSerializer(serializers.ModelSerializer):
    """DataSource serializer for creates/listings."""
    data_provider_id = serializers.ChoiceField(
        label=get_field(DataSource, 'data_provider_id').verbose_name,
        choices=[],  # filled in __init__
    )
    options = DataSourceOptionsListSerializer()

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

    def create(self, validated_data):
        options = validated_data.pop('options', None)
        with transaction.atomic():
            self.instance = DataSource.objects.create(**validated_data)
            self.fields['options'].create(validated_data=options)
        return self.instance


class DataSourceUpdateSerializer(DataSourceSerializer):
    """DataSource serializer for updates."""
    data_provider_id = serializers.ReadOnlyField(
        label=get_field(DataSource, 'data_provider_id').verbose_name,
    )

    def update(self, instance: DataSource, validated_data):
        options = validated_data.pop('options', None)
        if options is not None:
            self.fields['options'].update(instance, options)

        super().update(instance, validated_data=validated_data)

        return instance
