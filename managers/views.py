from rest_framework import generics, permissions
from managers.models import Manager
from managers.serializers import ManagerSerializer
from django.utils import timezone


class ManagerListView(generics.ListAPIView):
    """
    Admin / internal use
    """

    # queryset = Manager.objects.select_related("user").all()
    # .order_by("-month")
    serializer_class = ManagerSerializer

    # permission_classes = [permissions.IsAuthenticated]
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
    # permission_classes = [permissions.IsAuthenticated]
