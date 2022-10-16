from django.db import transaction, models
from rest_framework import serializers

from app.utils.models import get_field
from storage.base_data_provider import provider_registry
from storage.models import DataSource, DataSourceOption


class DatasourceDictField(serializers.DictField):
    def to_representation(self, value):
        iterable = value.all() if isinstance(value, models.Manager) else value

        return {
            item.key: item.value
            for item in iterable
        }


class DataSourceSerializer(serializers.ModelSerializer):
    """DataSource serializer for creates/listings."""
    data_provider_id = serializers.ChoiceField(
        label=get_field(DataSource, 'data_provider_id').verbose_name,
        choices=[],  # filled in __init__
    )
    # todo: nobody cares about key:value length (it is limited by DataSourceOption.key and .value)
    options = DatasourceDictField(required=True)

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
            provider_cls.validate_options(options=attrs)
        return attrs

    def create(self, validated_data):
        options = validated_data.pop('options', None)
        with transaction.atomic():
            self.instance = DataSource.objects.create(**validated_data)

            data_sources = [
                DataSourceOption(key=key, value=value, data_source=self.instance)
                for key, value in options.items()
            ]
            DataSourceOption.objects.bulk_create(data_sources)
        return self.instance


class DataSourceUpdateSerializer(DataSourceSerializer):
    """DataSource serializer for updates."""
    data_provider_id = serializers.ReadOnlyField(
        label=get_field(DataSource, 'data_provider_id').verbose_name,
    )

    def validate_options(self, attrs):
        data_provider_id = self.instance.data_provider_id
        provider_cls = provider_registry.get_provider(data_provider_id)
        provider_cls.validate_options(options=attrs)
        return attrs

    def update(self, instance: DataSource, validated_data):
        options = validated_data.pop('options', None)

        with transaction.atomic():
            if options is not None:
                data_sources = [
                    DataSourceOption(key=key, value=value, data_source=instance)
                    for key, value in options.items()
                ]
                instance.options.all().delete()
                DataSourceOption.objects.bulk_create(data_sources)

            super().update(instance, validated_data=validated_data)

        return instance
