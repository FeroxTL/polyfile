from django.db import transaction, models
from rest_framework import serializers, exceptions
from rest_framework.settings import api_settings
from rest_framework.utils import html

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

        if data_provider_id and provider_registry.has_provider(data_provider_id):
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

    def to_representation(self, data):
        """List if object instances -> Dict of primitive datatypes (key:value)."""
        iterable = data.all() if isinstance(data, models.Manager) else data

        return {
            item.key: item.value
            for item in iterable
        }

    def to_internal_value(self, data):
        """Dict of native values <- Dict of primitive datatypes."""
        if html.is_html_input(data):
            data = html.parse_html_list(data, default=[])

        if not isinstance(data, dict):
            # todo: not_a_dict
            message = self.error_messages['not_a_list'].format(
                input_type=type(data).__name__
            )
            raise exceptions.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='not_a_list')

        ret = []
        errors = []

        for key, item in data.items():
            try:
                validated = self.child.run_validation({'key': key, 'value': item})
            except exceptions.ValidationError as exc:
                errors.append(exc.detail)
            else:
                ret.append(validated)
                errors.append({})

        if any(errors):
            raise exceptions.ValidationError(errors)

        return ret


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
