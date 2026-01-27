from django.urls import path, include

urlpatterns = [
    path("managers/", include("managers.urls")),
    path("creators/", include("creators.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", include("ai_insights.urls")),
]
