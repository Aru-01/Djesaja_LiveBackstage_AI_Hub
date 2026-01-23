from rest_framework import serializers
from creators.models import Creator
from accounts.serializers import UserSerializer


class CreatorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    manager_username = serializers.CharField(
        source="manager.user.username", read_only=True
    )

    class Meta:
        model = Creator
        fields = [
            "id",
            "user",
            "manager",
            "manager_username",
            "estimated_bonus_contribution",
            "achieved_milestones",
            "diamonds",
            "valid_go_live_days",
            "live_duration",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
