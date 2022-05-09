from rest_framework import serializers

from accounts.models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'full_name',
            'is_superuser',
        ]
