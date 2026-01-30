from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from creators.models import Creator
from api.permissions import IsAdmin, IsManager
from collections import defaultdict
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ai_insights.models import (
    AITarget,
    AIManagerTarget,
    AIDailySummary,
)
from ai_insights.utils import (
    get_current_month,
    get_previous_month,
    normalize_actions,
    format_datetime,
    get_common_ai_data,
    get_alert_counts,
)


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

            if s.user.role == "MANAGER":
                # creator = creators_map.get(s.user.id)
                # if creator and creator.manager:
                #     manager_username = creator.manager.user.username

                data.append(
                    {
                        "username": s.user.username,
                        "role": s.user.role,
                        # "manager_username": manager_username,
                        "daily_summary": {
                            "summary": s.summary,
                            "reason": s.reason,
                            "suggested_action": normalize_actions(s.suggested_actions),
                            "alert_type": s.alert_type,
                            "alert_message": s.alert_message,
                            "priority": s.priority,
                            "status": s.status,
                            "updated_at": format_datetime(s.updated_at),
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
                        "alert_message": s.alert_message,
                        "priority": s.priority,
                        "status": s.status,
                        "updated_at": format_datetime(s.updated_at),
                    },
                }
            )

        return Response(data)


class AlertsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Alerts",
        operation_description=(
            "Role-based alerts view:\n"
            "- **ADMIN / SUPER_ADMIN**: See all alerts from all managers.\n"
            "- **MANAGER**: See all alerts from all their creators.\n\n"
            "Each alert includes type, priority, message, user info, and last updated datetime."
        ),
        tags=["Alerts"],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "username": openapi.Schema(type=openapi.TYPE_STRING),
                        "role": openapi.Schema(type=openapi.TYPE_STRING),
                        "alert_type": openapi.Schema(type=openapi.TYPE_STRING),
                        "priority": openapi.Schema(type=openapi.TYPE_STRING),
                        "alert_message": openapi.Schema(type=openapi.TYPE_STRING),
                        "updated_at": openapi.Schema(type=openapi.FORMAT_DATETIME),
                    },
                ),
            ),
            403: "Permission denied",
        },
    )
    def get(self, request):
        user = request.user
        current_month = get_current_month()
        data = []

        # Helper to fetch alerts for a list of users
        def fetch_alerts(users, role_name):
            user_ids = [u.id for u in users]
            alerts_qs = AIDailySummary.objects.filter(
                user__in=user_ids, report_month=current_month
            ).order_by("-updated_at")

            alerts_by_user = defaultdict(list)
            for a in alerts_qs:
                alerts_by_user[a.user_id].append(a)

            alerts_list = []
            for u in users:
                for a in alerts_by_user.get(u.id, []):
                    alerts_list.append(
                        {
                            "user_id": u.id,
                            "username": u.username,
                            "role": role_name,
                            "alert_type": a.alert_type,
                            "priority": a.priority,
                            "alert_message": a.alert_message,
                            "updated_at": format_datetime(a.updated_at),
                        }
                    )
            return alerts_list

        # ---------------- ADMIN / SUPER_ADMIN ----------------
        if user.role in ["ADMIN", "SUPER_ADMIN"]:
            # own alerts
            data.extend(fetch_alerts([user], user.role))
            # all manager alerts
            managers = User.objects.filter(role="MANAGER")
            data.extend(fetch_alerts(managers, "MANAGER"))
            users_for_counter = list(managers) + [user]

        # ---------------- MANAGER ----------------
        elif user.role == "MANAGER":
            # own alerts
            data.extend(fetch_alerts([user], "MANAGER"))
            # all creator alerts under this manager
            creators_qs = User.objects.filter(
                creator_profile__manager__user=user,
                creator_profile__report_month=current_month,
            ).distinct()

            data.extend(fetch_alerts(creators_qs, "CREATOR"))
            users_for_counter = list(creators_qs) + [user]

        # ---------------- CREATOR ----------------
        elif user.role == "CREATOR":
            data.extend(fetch_alerts([user], "CREATOR"))
            users_for_counter = [user]

        else:
            return Response({"detail": "Permission denied"}, status=403)

        alert_counts = get_alert_counts(users_for_counter, current_month)

        return Response({"alert_counts": alert_counts, "alerts": data})
