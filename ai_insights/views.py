from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from ai_insights.models import (
    AITarget,
    AIMessage,
    AIDailySummary,
    AIScenario,
    AIMetric,
)
from ai_insights.serializers import (
    AITargetSerializer,
    AIMessageSerializer,
    AIDailySummarySerializer,
    AIScenarioSerializer,
    AIMetricSerializer,
)
from api.models import ReportingMonth
from django.utils.timezone import now


class CreatorAIDashboardTestAPIView(APIView):
    """
    Testing endpoint: returns all creator AI data (monthly + daily)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = ReportingMonth.objects.get(code="202512")

        if not month:
            return Response({"error": "No reporting month found"}, status=404)

        # All creator data
        creator_users = User.objects.filter(role="CREATOR")

        targets = AITarget.objects.filter(
            report_month=month,
            user__in=creator_users,
        ).select_related("user")

        summaries = AIDailySummary.objects.filter(
            report_month=month,
            user__in=creator_users,
        ).select_related("user")

        scenarios = AIScenario.objects.filter(
            report_month=month,
            user__in=creator_users,
        ).select_related("user")

        metrics = AIMetric.objects.filter(
            report_month=month,
            user__in=creator_users,
        ).select_related("user")

        messages = (
            AIMessage.objects.filter(
                user__in=creator_users,
                expires_at__gt=now(),
            )
            .order_by("-created_at")
            .select_related("user")
        )

        return Response(
            {
                "targets": AITargetSerializer(targets, many=True).data,
                "summaries": AIDailySummarySerializer(summaries, many=True).data,
                "scenarios": AIScenarioSerializer(scenarios, many=True).data,
                "metrics": AIMetricSerializer(metrics, many=True).data,
                "messages": AIMessageSerializer(messages, many=True).data,
            }
        )


class ManagerAIDashboardTestAPIView(APIView):
    """
    Testing endpoint: returns all manager AI data
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = ReportingMonth.objects.get(code="202512")
        if not month:
            return Response({"error": "No reporting month found"}, status=404)

        manager_users = User.objects.filter(role="MANAGER")

        summaries = AIDailySummary.objects.filter(
            report_month=month,
            user__in=manager_users,
        ).select_related("user")

        messages = (
            AIMessage.objects.filter(
                user__in=manager_users,
                expires_at__gt=now(),
            )
            .order_by("-created_at")
            .select_related("user")
        )
        targets = AITarget.objects.filter(
            report_month=month,
            user__in=manager_users,
        ).select_related("user")

        return Response(
            {
                "targets": AITargetSerializer(targets, many=True).data,
                "summaries": AIDailySummarySerializer(summaries, many=True).data,
                "messages": AIMessageSerializer(messages, many=True).data,
            }
        )


class AdminAIOverviewTestAPIView(APIView):
    """
    Testing endpoint: returns full AI data for admin inspection
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = ReportingMonth.objects.order_by("-year", "-month").first()
        if not month:
            return Response({"error": "No reporting month found"}, status=404)

        admin_user = User.objects.filter(username="admin").first()
        if not admin_user:
            return Response({"error": "Admin user not found"}, status=404)

        targets = AITarget.objects.filter(
            report_month=month,
            user=admin_user,
        ).select_related("user")

        summaries = AIDailySummary.objects.filter(
            report_month=month,
            user=admin_user,
        ).select_related("user")

        scenarios = AIScenario.objects.filter(
            report_month=month,
            user=admin_user,
        ).select_related("user")

        metrics = AIMetric.objects.filter(
            report_month=month,
            user=admin_user,
        ).select_related("user")

        messages = (
            AIMessage.objects.filter(
                user=admin_user,
                expires_at__gt=now(),
            )
            .order_by("-created_at")
            .select_related("user")
        )

        return Response(
            {
                "month": month.code,
                "targets": AITargetSerializer(targets, many=True).data,
                "summaries": AIDailySummarySerializer(summaries, many=True).data,
                "scenarios": AIScenarioSerializer(scenarios, many=True).data,
                "metrics": AIMetricSerializer(metrics, many=True).data,
                "messages": AIMessageSerializer(messages, many=True).data,
            }
        )


# class CreatorAIDashboardAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         month = ReportingMonth.objects.order_by("-year", "-month").first()
#         if not month:
#             return Response({"error": "No reporting month found"}, status=404)

#         target = AITarget.objects.filter(user=user, report_month=month).first()
#         summary = AIDailySummary.objects.filter(user=user, report_month=month).first()
#         scenario = AIScenario.objects.filter(user=user, report_month=month).first()
#         metrics = AIMetric.objects.filter(user=user, report_month=month)
#         messages = AIMessage.objects.filter(user=user, expires_at__gt=now()).order_by(
#             "-created_at"
#         )

#         return Response(
#             {
#                 "target": AITargetSerializer(target).data if target else None,
#                 "summary": AIDailySummarySerializer(summary).data if summary else None,
#                 "scenario": AIScenarioSerializer(scenario).data if scenario else None,
#                 "metrics": AIMetricSerializer(metrics, many=True).data,
#                 "messages": AIMessageSerializer(messages, many=True).data,
#             }
#         )


# class ManagerAIDashboardAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         month = ReportingMonth.objects.order_by("-year", "-month").first()
#         if not month:
#             return Response({"error": "No reporting month found"}, status=404)

#         summary = AIDailySummary.objects.filter(user=user, report_month=month).first()

#         messages = AIMessage.objects.filter(
#             user=user,
#             expires_at__gt=now(),
#         )

#         return Response(
#             {
#                 "summary": AIDailySummarySerializer(summary).data if summary else None,
#                 "messages": AIMessageSerializer(messages, many=True).data,
#             }
#         )


# class AdminAIOverviewAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         month = ReportingMonth.objects.order_by("-year", "-month").first()
#         if not month:
#             return Response({"error": "No reporting month found"}, status=404)

#         high_priority_alerts = AIDailySummary.objects.filter(
#             report_month=month, priority="high"
#         ).count()

#         creators_at_risk = AIDailySummary.objects.filter(
#             report_month=month,
#             alert_type__isnull=False,
#         ).count()

#         return Response(
#             {
#                 "month": month.code,
#                 "high_priority_alerts": high_priority_alerts,
#                 "creators_at_risk": creators_at_risk,
#             }
#         )
