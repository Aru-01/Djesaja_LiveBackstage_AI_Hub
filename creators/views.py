from rest_framework import generics, permissions
from creators.models import Creator
from creators.serializers import CreatorSerializer
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CreatorListView(generics.ListAPIView):
    serializer_class = CreatorSerializer

    # permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="List Creators (Filter by Manager & Month)",
        tags=["Creators"],
        manual_parameters=[
            openapi.Parameter(
                name="manager_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Filter creators by manager ID",
                required=False,
            ),
            openapi.Parameter(
                name="month",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Report month in YYYYMM format (default: current month)",
                required=False,
                example="202501",
            ),
        ],
        responses={200: CreatorSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Creator.objects.select_related(
            "user",
            "manager",
            "manager__user",
        )

        # ----------------- Filters -----------------
        manager_id = self.request.query_params.get("manager_id")
        month = self.request.query_params.get("month")

        # Default current month
        if not month:
            month = timezone.now().strftime("%Y%m")

        queryset = queryset.filter(report_month__code=month)

        if manager_id:
            queryset = queryset.filter(manager_id=manager_id)

        return queryset


class CreatorDetailView(generics.RetrieveAPIView):
    queryset = Creator.objects.select_related(
        "user",  # creator.user
        "manager",  # creator.manager
        "manager__user",  # manager.user
    ).all()
    serializer_class = CreatorSerializer

    # permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get Creator Details",
        tags=["Creators"],
        responses={
            200: CreatorSerializer,
            404: "Creator not found",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
