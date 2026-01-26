from django.urls import path
from ai_insights.views import (
    CreatorAIDashboardTestAPIView,
    ManagerAIDashboardTestAPIView,
    AdminAIOverviewTestAPIView,
)

urlpatterns = [
    path("ai-response/creator/", CreatorAIDashboardTestAPIView.as_view()),
    path("ai-response/manager/", ManagerAIDashboardTestAPIView.as_view()),
    path("ai-response/admin/", AdminAIOverviewTestAPIView.as_view()),
]
