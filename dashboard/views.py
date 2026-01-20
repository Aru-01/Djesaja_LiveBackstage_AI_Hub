# dashboard/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from dashboard.utils import (
    admin_dashboard_data,
    get_creators_data,
    get_managers_data,
    get_report_month,
)
from dashboard.serializers import (
    AdminDashboardSerializer,
    ManagerDashboardSerializer,
    CreatorDashboardSerializer,
)
from api.models import ReportingMonth


class AdminDashboardView(APIView):
    """
    Admin dashboard
    Optional query param: month=YYYYMM
    Example: /api/dashboard/admin/?month=202601
    """

    # permission_classes = [IsAuthenticated]  # Optional, can comment

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
    """
    GET /api/dashboard/manager/?month=202601  -> all managers
    GET /api/dashboard/manager/?month=202601&manager_id=5 -> single manager
    """

    def get(self, request):
        month_code = request.GET.get("month")
        manager_id = request.GET.get("manager_id")

        try:
            report_month = get_report_month(month_code)
        except ReportingMonth.DoesNotExist:
            return Response({"error": "Invalid month code"}, status=400)

        data = get_managers_data(report_month, manager_id=manager_id)
        serializer = ManagerDashboardSerializer(data, many=True)
        return Response(serializer.data)


class CreatorDashboardView(APIView):
    """
    GET /api/dashboard/creator/?month=202601 -> all creators
    GET /api/dashboard/creator/?month=202601&creator_id=10 -> single creator
    """

    def get(self, request):
        month_code = request.GET.get("month")
        creator_id = request.GET.get("creator_id")

        try:
            report_month = get_report_month(month_code)
        except ReportingMonth.DoesNotExist:
            return Response({"error": "Invalid month code"}, status=400)

        data = get_creators_data(report_month, creator_id=creator_id)
        serializer = CreatorDashboardSerializer(data, many=True)
        return Response(serializer.data)
