from django.contrib import admin
from django.urls import include
from django.urls import path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", include("df_chat.drf.urls")),
    path("api/auth/", include("df_auth.drf.urls")),
    path("chat/", include("df_chat.urls")),
]
