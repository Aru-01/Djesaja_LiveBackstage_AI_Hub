from rest_framework import serializers
from ai_insights.models import (
    AITarget,
    AIMessage,
    AIDailySummary,
    AIScenario,
    AIMetric,
)
from accounts.models import User
from creators.models import Creator
from managers.models import Manager


class SimpleUserSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "role", "manager_name"]

    def get_manager_name(self, obj):
        if obj.role == "CREATOR":
            creator = obj.creator_profile.first()
            if creator and creator.manager:
                return creator.manager.user.username
        return None


# class UserInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["username", "role"]


class AITargetSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = AITarget
        fields = [
            "user",
            "target_milestone",
            "target_diamonds",
            "reward_status",
            "expires_at",
        ]


class AIMessageSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = AIMessage
        fields = [
            "user",
            "message_type",
            "message",
            "expires_at",
            "created_at",
        ]


class AIDailySummarySerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = AIDailySummary
        fields = [
            "user",
            "summary",
            "reason",
            "suggested_actions",
            "alert_type",
            "priority",
            "status",
        ]


class AIScenarioSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = AIScenario
        fields = ["user", "data"]


class AIMetricSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = AIMetric
        fields = ["user", "key", "value"]
