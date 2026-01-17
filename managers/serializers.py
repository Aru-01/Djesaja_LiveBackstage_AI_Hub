from rest_framework import serializers
from managers.models import Manager
from accounts.serializers import UserSerializer


class ManagerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Manager
        fields = [
            "id",
            "user",
            "name",
            "month",
            "eligible_creators",
            "estimated_bonus_contribution",
            "diamonds",
            "M_0_5",
            "M1",
            "M2",
            "M1R",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
