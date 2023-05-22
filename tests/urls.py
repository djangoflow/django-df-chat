from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions


# Swagger UI schema configuration.
schema_view = get_schema_view(
    openapi.Info(
        title="Djangoflow Chat",
        default_version="0.0.1",
        description="Swagger UI for Djangoflow Chat API schema.",
    ),
    permission_classes=[
        permissions.AllowAny,
    ],
    public=True,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Route for Swagger UI
    path("swagger/",
         schema_view.with_ui("swagger", cache_timeout=0)),
    path("api/v1/chat/", include("df_chat.drf.urls")),
    path("api/v1/auth/", include("df_auth.drf.urls")),
    path("chat/", include("df_chat.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
