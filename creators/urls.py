from django.urls import path
from creators.views import CreatorListView, CreatorDetailView

urlpatterns = [
    path("", CreatorListView.as_view(), name="creator-list"),
    path("<int:pk>/", CreatorDetailView.as_view(), name="creator-detail"),
]
