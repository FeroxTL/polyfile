from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.base_data_provider import provider_registry


class DataProviderList(APIView):
    """Data provider list with parameters for each one."""
    permission_classes = [permissions.IsAdminUser]

    @staticmethod
    def _get_provider_fields(provider_class):
        return [
            {
                'attribute': key,
                'type': field.widget.input_type,
                'required': field.required,
                'read_only': field.disabled,
                'label': field.label or key.capitalize(),
                'help_text': field.help_text,
            }
            for key, field in provider_class.validation_class().fields.items()
        ]

    def _get_provider_data(self, provider_class):
        return {
            'id': provider_class.provider_id,
            'fields': self._get_provider_fields(provider_class=provider_class)
        }

    def get(self, request):
        """Retrieve provider info."""
        return Response([
            self._get_provider_data(provider_class=provider_class)
            for provider_class in provider_registry.providers
        ])
