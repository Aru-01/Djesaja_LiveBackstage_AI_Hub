from django.urls import path
from managers.views import ManagerListView, ManagerDetailView

urlpatterns = [
    path("", ManagerListView.as_view(), name="manager-list"),
    path("<int:pk>/", ManagerDetailView.as_view(), name="manager-detail"),
]
