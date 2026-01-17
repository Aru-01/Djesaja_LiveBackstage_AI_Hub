from rest_framework import generics, permissions
from managers.models import Manager
from managers.serializers import ManagerSerializer


class ManagerListView(generics.ListAPIView):
    """
    Admin / internal use
    """

    queryset = Manager.objects.select_related("user").all().order_by("-month")
    serializer_class = ManagerSerializer
    # permission_classes = [permissions.IsAuthenticated]


class ManagerDetailView(generics.RetrieveAPIView):
    queryset = Manager.objects.select_related("user").all()
    serializer_class = ManagerSerializer
    # permission_classes = [permissions.IsAuthenticated]
