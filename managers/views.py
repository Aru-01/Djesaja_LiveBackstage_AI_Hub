from rest_framework import generics, permissions
from managers.models import Manager
from managers.serializers import ManagerSerializer
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ManagerListView(generics.ListAPIView):
    """
    Admin / internal use
    """

    # queryset = Manager.objects.select_related("user").all()
    # .order_by("-month")
    serializer_class = ManagerSerializer

    @swagger_auto_schema(
        operation_summary="List Managers (Admin / Internal)",
        tags=["Managers"],
        manual_parameters=[
            openapi.Parameter(
                name="month",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Report month in YYYYMM format (default: current month)",
                example="202501",
            ),
        ],
        responses={200: ManagerSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Manager.objects.select_related("user")
        month = self.request.query_params.get("month")
        if not month:
            month = timezone.now().strftime("%Y%m")
        queryset = queryset.filter(report_month__code=month)
        return queryset


class ManagerDetailView(generics.RetrieveAPIView):
    queryset = Manager.objects.select_related("user").all()
    serializer_class = ManagerSerializer

    @swagger_auto_schema(
        operation_summary="Get Manager Details",
        tags=["Managers"],
        responses={
            200: ManagerSerializer,
            404: "Manager not found",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
