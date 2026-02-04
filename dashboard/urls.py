from django.urls import path
from dashboard.views import (
    AdminDashboardView,
    ManagerDashboardView,
    CreatorDashboardView,
    CreatorRankView,
)

urlpatterns = [
    path("admin/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("manager/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    path("creator/", CreatorDashboardView.as_view(), name="creator-dashboard"),
    path(
        "creator/rank/",
        CreatorRankView.as_view(),
        name="creator-rank",
    ),
]
