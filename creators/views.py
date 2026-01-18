from rest_framework import generics, permissions
from creators.models import Creator
from creators.serializers import CreatorSerializer
from django.utils import timezone


class CreatorListView(generics.ListAPIView):
    serializer_class = CreatorSerializer
    # permission_classes = [permissions.IsAuthenticated]

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
