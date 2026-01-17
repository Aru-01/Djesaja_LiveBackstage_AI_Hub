from rest_framework import serializers
from creators.models import Creator
from accounts.serializers import UserSerializer


class CreatorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    manager_name = serializers.CharField(source="manager.name", read_only=True)

    class Meta:
        model = Creator
        fields = [
            "id",
            "user",
            "manager",
            "manager_name",
            "name",
            "month",
            "estimated_bonus_contribution",
            "achieved_milestones",
            "diamonds",
            "valid_go_live_days",
            "live_duration",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
