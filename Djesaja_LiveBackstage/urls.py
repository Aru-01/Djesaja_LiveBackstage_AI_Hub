from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Top Talent Agency",
        default_version="v1",
        description="""The LiveBackstage Automation System is a fully custom-built AI and data
                        automation platform designed for TikTok Live agencies to streamline creator
                        management, performance tracking, and daily reporting — without repetitive
                        manual work.""",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="toptalentagency@support.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("api-auth/", include("rest_framework.urls")),
        path("auth/", include("accounts.urls")),
        path("api/", include("api.urls")),
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + debug_toolbar_urls()
)
