from rest_framework import serializers
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "profile_image",
            "role",
            "is_active",
        ]
        read_only_fields = ["id"]
