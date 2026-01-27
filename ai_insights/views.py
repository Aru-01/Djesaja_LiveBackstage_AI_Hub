from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from ai_insights.models import (
    AITarget,
    AIManagerTarget,
    AIMessage,
    AIDailySummary,
    AIScenario,
    AIMetric,
)
from api.models import ReportingMonth
from creators.models import Creator
from datetime import datetime, timedelta
from api.models import ReportingMonth
from api.permissions import IsAdmin, IsCreator, IsManager
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def get_current_month():
    code = datetime.now().strftime("%Y%m")
    return ReportingMonth.objects.get(code=code)


def get_previous_month():
    first_day = datetime.now().replace(day=1)
    prev_month = first_day - timedelta(days=1)
    return ReportingMonth.objects.get(code=prev_month.strftime("%Y%m"))


def normalize_actions(actions):
    if not actions:
        return []
    if isinstance(actions, list):
        return actions
    return [actions]


def get_common_ai_data(user, report_month):
    msg = (
        AIMessage.objects.filter(user=user, expires_at__gte=timezone.now())
        .order_by("-created_at")
        .first()
    )

    summary = AIDailySummary.objects.filter(
        user=user, report_month=report_month
    ).first()

    scenario = AIScenario.objects.filter(user=user, report_month=report_month).first()

    metric = AIMetric.objects.filter(user=user, report_month=report_month).first()

    return {
        "welcome_msg": {
            "msg_type": msg.message_type if msg else None,
            "msg": msg.message if msg else None,
        },
        "daily_summary": {
            "summary": summary.summary if summary else None,
            "reason": summary.reason if summary else None,
            "suggested_action": (
                normalize_actions(summary.suggested_actions) if summary else []
            ),
            "alert_type": summary.alert_type if summary else None,
            "priority": summary.priority if summary else None,
            "status": summary.status if summary else None,
        },
        "scenarios": scenario.data if scenario else {},
        "metrics": metric.data if metric else {},
    }


class AIResponseView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get AI Dashboard Response (Role Based)",
        operation_description=(
            "Returns AI-generated dashboard data based on user role.\n\n"
            "- **CREATOR**: manager info, previous month target, AI insights\n"
            "- **MANAGER**: team target, AI insights\n"
            "- **ADMIN / SUPER_ADMIN**: AI insights only\n\n"
            "Data is calculated using current and previous reporting months automatically."
        ),
        tags=["AI-Response"],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "username": openapi.Schema(type=openapi.TYPE_STRING),
                            "role": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                    "manager": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "username": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                    "target": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "diamonds": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "milestone": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                    "welcome_msg": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "msg_type": openapi.Schema(type=openapi.TYPE_STRING),
                            "msg": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                    "daily_summary": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "summary": openapi.Schema(type=openapi.TYPE_STRING),
                            "reason": openapi.Schema(type=openapi.TYPE_STRING),
                            "suggested_action": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Items(type=openapi.TYPE_STRING),
                            ),
                            "alert_type": openapi.Schema(type=openapi.TYPE_STRING),
                            "priority": openapi.Schema(type=openapi.TYPE_STRING),
                            "status": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                    "scenarios": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "metrics": openapi.Schema(type=openapi.TYPE_OBJECT),
                },
            ),
            401: "Unauthorized",
        },
    )
    def get(self, request):
        user = request.user
        current_month = get_current_month()
        prev_month = get_previous_month()

        # basic user info
        response = {
            "user": {
                "username": user.username,
                "role": user.role,
            }
        }

        # ======== CREATOR ========
        if user.role == "CREATOR":
            creator = (
                Creator.objects.filter(user=user, report_month=current_month)
                .select_related("manager__user")
                .first()
            )
            # prev month target
            target = AITarget.objects.filter(user=user, report_month=prev_month).first()

            # manager info
            response["manager"] = {
                "username": (
                    creator.manager.user.username
                    if creator and creator.manager
                    else None
                )
            }

            # prev month target info
            response["target"] = {
                "diamonds": target.target_diamonds if target else 0,
                "milestone": target.target_milestone if target else None,
            }

            # own AI data
            response.update(get_common_ai_data(user, current_month))

        # ======== MANAGER ========
        elif user.role == "MANAGER":
            # prev month target
            target = AIManagerTarget.objects.filter(
                user=user, report_month=prev_month
            ).first()
            response["target"] = {
                "diamonds": target.team_target_diamonds if target else 0
            }

            # own data
            response.update(get_common_ai_data(user, current_month))

        # ======== ADMIN ========
        elif user.role in ["ADMIN", "SUPER_ADMIN"]:
            # own data
            response.update(get_common_ai_data(user, current_month))

        return Response(response)


class AdminDailySummaryOverview(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @swagger_auto_schema(
        operation_summary="Admin Daily Summary Overview",
        operation_description=(
            "Returns daily AI summaries for all users in the current reporting month.\n\n"
            "- Includes creator → manager mapping\n"
            "- Admin-only endpoint"
        ),
        tags=["AI-Response - Admin"],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "username": openapi.Schema(type=openapi.TYPE_STRING),
                        "role": openapi.Schema(type=openapi.TYPE_STRING),
                        "manager_username": openapi.Schema(
                            type=openapi.TYPE_STRING, nullable=True
                        ),
                        "daily_summary": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "summary": openapi.Schema(type=openapi.TYPE_STRING),
                                "reason": openapi.Schema(type=openapi.TYPE_STRING),
                                "suggested_action": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Items(type=openapi.TYPE_STRING),
                                ),
                                "alert_type": openapi.Schema(type=openapi.TYPE_STRING),
                                "priority": openapi.Schema(type=openapi.TYPE_STRING),
                                "status": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            403: "Permission denied",
        },
    )
    def get(self, request):
        current_month = get_current_month()

        summaries = AIDailySummary.objects.filter(
            report_month=current_month
        ).select_related("user")

        creators_map = {
            c.user_id: c
            for c in Creator.objects.filter(report_month=current_month).select_related(
                "manager__user"
            )
        }

        data = []

        for s in summaries:
            manager_username = None

            if s.user.role == "CREATOR":
                creator = creators_map.get(s.user.id)
                if creator and creator.manager:
                    manager_username = creator.manager.user.username

            data.append(
                {
                    "username": s.user.username,
                    "role": s.user.role,
                    "manager_username": manager_username,
                    "daily_summary": {
                        "summary": s.summary,
                        "reason": s.reason,
                        "suggested_action": normalize_actions(s.suggested_actions),
                        "alert_type": s.alert_type,
                        "priority": s.priority,
                        "status": s.status,
                    },
                }
            )

        return Response(data)


class ManagerCreatorsDailySummaryView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        operation_summary="Manager Creators Daily Summary",
        operation_description=(
            "Returns daily AI summaries of all creators under the authenticated manager "
            "for the current reporting month."
        ),
        tags=["AI-Response - Manager"],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "creator_username": openapi.Schema(type=openapi.TYPE_STRING),
                        "daily_summary": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "summary": openapi.Schema(type=openapi.TYPE_STRING),
                                "reason": openapi.Schema(type=openapi.TYPE_STRING),
                                "suggested_action": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Items(type=openapi.TYPE_STRING),
                                ),
                                "alert_type": openapi.Schema(type=openapi.TYPE_STRING),
                                "priority": openapi.Schema(type=openapi.TYPE_STRING),
                                "status": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            403: "Permission denied",
        },
    )
    def get(self, request):
        manager_user = request.user
        current_month = get_current_month()

        creators = Creator.objects.filter(
            manager__user=manager_user, report_month=current_month
        ).select_related("user")

        summaries = AIDailySummary.objects.filter(
            user__in=[c.user for c in creators], report_month=current_month
        ).select_related("user")

        data = []

        for s in summaries:
            data.append(
                {
                    "creator_username": s.user.username,
                    "daily_summary": {
                        "summary": s.summary,
                        "reason": s.reason,
                        "suggested_action": normalize_actions(s.suggested_actions),
                        "alert_type": s.alert_type,
                        "priority": s.priority,
                        "status": s.status,
                    },
                }
            )

        return Response(data)
