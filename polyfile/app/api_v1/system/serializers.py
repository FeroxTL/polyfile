from rest_framework import serializers

from accounts.models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serializer for current_user view."""
    class Meta:
        model = User
        fields = [
            'full_name',
            'is_superuser',
        ]
