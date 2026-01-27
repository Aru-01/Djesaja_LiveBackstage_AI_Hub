from django.urls import path
from ai_insights.views import (
    AIResponseView,
    AdminDailySummaryOverview,
    ManagerCreatorsDailySummaryView,
)

urlpatterns = [
    path("ai-response/", AIResponseView.as_view()),
    path("ai-response/admin-overview/", AdminDailySummaryOverview.as_view()),
    path("ai-response/manager-overview/", ManagerCreatorsDailySummaryView.as_view()),
]
