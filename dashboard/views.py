from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from dashboard.utils import (
    admin_dashboard_data,
    get_creators_data,
    get_managers_data,
)
from dashboard.helpers import get_report_month
from dashboard.serializers import (
    AdminDashboardSerializer,
    ManagerDashboardSerializer,
    CreatorDashboardSerializer,
)
from creators.models import Creator
from api.permissions import IsAdmin, IsCreator, IsManager
from api.models import ReportingMonth
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def get_latest_report_month():
    now = timezone.now()
    month_code = f"{now.year}{now.month:02d}"
    return ReportingMonth.objects.get(code=month_code)


class AdminDashboardView(APIView):
    """
    Admin dashboard
    Optional query param: month=YYYYMM
    """

    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_summary="Admin Dashboard Overview",
        tags=["Dashboards"],
        manual_parameters=[
            openapi.Parameter(
                name="month",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Report month in YYYYMM format (default: current month)",
                example="202601",
            ),
        ],
        responses={
            200: AdminDashboardSerializer,
            400: "Invalid month code",
        },
    )
    def get(self, request):
        month_code = request.GET.get("month")
        try:
            report_month = get_report_month(month_code)
        except ReportingMonth.DoesNotExist:
            return Response({"error": "Invalid month code"}, status=400)

        data = admin_dashboard_data(report_month)
        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)


class ManagerDashboardView(APIView):
    permission_classes = [IsManager | IsAdmin]

    @swagger_auto_schema(
        operation_summary="Manager Dashboard",
        tags=["Dashboards"],
        manual_parameters=[
            openapi.Parameter(
                name="month",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Report month (Admin only) - YYYYMM",
                example="202601",
            ),
            openapi.Parameter(
                name="manager_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="Manager ID (Admin only, optional)",
            ),
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Search by username (optional)",
            ),
        ],
        responses={
            200: ManagerDashboardSerializer(many=True),
            400: "Invalid month code",
            404: "Manager data not found",
        },
    )
    def get(self, request):

        month_code = request.GET.get("month")
        search = request.GET.get("search")
        try:
            report_month = get_report_month(month_code)
        except ReportingMonth.DoesNotExist:
            return Response({"error": "Invalid month code"}, status=400)

        if request.user.role == "MANAGER":
            manager = request.user.manager_profile.filter(
                report_month=report_month
            ).first()
            if not manager:
                return Response(
                    {"error": "Manager data not found for this month"}, status=404
                )
            manager_id = manager.id
            data = get_managers_data(report_month, manager_id=manager_id)

        elif request.user.role in "SUPER_ADMIN":
            manager_id = request.GET.get("manager_id")
            data = get_managers_data(report_month, manager_id=manager_id, search=search)

        else:
            return Response({"error": "Unauthorized"}, status=403)

        serializer = ManagerDashboardSerializer(
            data,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class CreatorDashboardView(APIView):
    permission_classes = [IsCreator | IsManager | IsAdmin]

    @swagger_auto_schema(
        operation_summary="Creator Dashboard",
        tags=["Dashboards"],
        manual_parameters=[
            openapi.Parameter(
                name="month",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Report month in YYYYMM format",
                example="202601",
            ),
            openapi.Parameter(
                name="creator_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="Filter by Creator ID (Admin only or Manager)",
            ),
            openapi.Parameter(
                name="manager_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="Filter creators by Manager ID (Admin only)",
            ),
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Search creators by username (Admin/Manager/Creator)",
            ),
        ],
        responses={200: CreatorDashboardSerializer(many=True)},
    )
    def get(self, request):
        month_code = request.GET.get("month")
        creator_id = request.GET.get("creator_id")
        manager_id = request.GET.get("manager_id")
        search = request.GET.get("search")

        try:
            report_month = get_report_month(month_code)
        except ReportingMonth.DoesNotExist:
            return Response({"error": "Invalid month code"}, status=400)

        user = request.user

        # ================= CREATOR =================
        if user.role == "CREATOR":
            creator = user.creator_profile.filter(report_month=report_month).first()
            if not creator:
                return Response({"error": "Creator data not found"}, status=404)

            data = get_creators_data(
                report_month,
                creator_id=creator.id,
                manager_id=creator.manager.id,
                search=search,
            )

        # ================= MANAGER =================
        elif user.role == "MANAGER":
            manager = user.manager_profile.filter(report_month=report_month).first()
            if not manager:
                return Response({"error": "Manager data not found"}, status=404)

            data = get_creators_data(
                report_month,
                manager_id=manager.id,
                creator_id=creator_id,
                search=search,
            )

        # ================= ADMIN =================
        elif user.role == "SUPER_ADMIN":

            if creator_id:
                creator = (
                    Creator.objects.filter(id=creator_id, report_month=report_month)
                    .select_related("manager")
                    .first()
                )
                if not creator:
                    return Response({"error": "Creator data not found"}, status=404)

                data = get_creators_data(
                    report_month,
                    creator_id=creator.id,
                    manager_id=creator.manager.id,
                    search=search,
                )

            else:
                # fetch all creators, optionally filter by manager_id and/or search
                data = get_creators_data(
                    report_month,
                    manager_id=manager_id,
                    search=search,
                )

        else:
            return Response({"error": "Unauthorized"}, status=403)

        serializer = CreatorDashboardSerializer(
            data, many=True, context={"request": request}
        )
        return Response(serializer.data)
