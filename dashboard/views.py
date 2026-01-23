from django.utils import timezone
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


def get_latest_report_month():
    now = timezone.now()
    month_code = f"{now.year}{now.month:02d}"
    return ReportingMonth.objects.get(code=month_code)


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

    def get(self, request):

        # 🔐 Logged-in manager
        if request.user.is_authenticated and request.user.role == "MANAGER":
            report_month = get_latest_report_month()
            manager = request.user.manager_profile.filter(
                report_month=report_month
            ).first()

            if not manager:
                return Response(
                    {"error": "Manager data not found for this month"}, status=404
                )

            manager_id = manager.id

        else:
            # 🌐 Admin / public
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
    - Logged-in creator → own dashboard (latest month)
    - Logged-in manager → own creators dashboard (latest month)
    - Admin/public → all or single creator (month optional)
    """

    def get(self, request):

        # 🔐 Logged-in creator
        if request.user.is_authenticated and request.user.role == "CREATOR":
            report_month = get_latest_report_month()
            creator = request.user.creator_profile.filter(
                report_month=report_month
            ).first()

            if not creator:
                return Response(
                    {"error": "Creator data not found for this month"}, status=404
                )

            creator_id = creator.id
            data = get_creators_data(report_month, creator_id=creator_id)

        # 🔐 Logged-in manager → only own creators
        elif request.user.is_authenticated and request.user.role == "MANAGER":
            report_month = get_latest_report_month()
            manager = request.user.manager_profile.filter(
                report_month=report_month
            ).first()

            if not manager:
                return Response(
                    {"error": "Manager data not found for this month"}, status=404
                )

            # manager_id passed to utils to get all creators under this manager
            data = get_creators_data(report_month, manager_id=manager.id)

        # 🌐 Admin / public
        else:
            month_code = request.GET.get("month")
            creator_id = request.GET.get("creator_id")

            try:
                report_month = get_report_month(month_code)
            except ReportingMonth.DoesNotExist:
                return Response({"error": "Invalid month code"}, status=400)

            data = get_creators_data(report_month, creator_id=creator_id)

        serializer = CreatorDashboardSerializer(data, many=True)
        return Response(serializer.data)
