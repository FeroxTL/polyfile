from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.data_providers.base import provider_registry


class DataProviderList(APIView):
    permission_classes = [permissions.IsAdminUser]

    @staticmethod
    def get_provider_fields(provider_class):
        fields = {}
        for key, field in provider_class.validation_class().fields.items():
            fields[key] = {
                'type': field.widget.input_type,
                'required': field.required,
                'read_only': field.disabled,
                'label': field.label or key.capitalize(),
            }

        return fields

    def get_provider_description(self, provider_class):
        return {
            'id': provider_class.provider_id,
            'fields': self.get_provider_fields(provider_class=provider_class)
        }

    def get(self, request):
        return Response([
            self.get_provider_description(provider_class=provider_class)
            for provider_class in provider_registry.providers
        ])
