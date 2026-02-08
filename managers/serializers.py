from rest_framework import serializers
from managers.models import Manager
from accounts.serializers import UserSerializer


class ManagerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    manager_uid = serializers.CharField(default="", allow_null=True)

    class Meta:
        model = Manager
        fields = [
            "id",
            "user",
            "manager_uid",
            "eligible_creators",
            "estimated_bonus_contribution",
            "diamonds",
            "M_0_5",
            "M1",
            "M2",
            "M1R",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
