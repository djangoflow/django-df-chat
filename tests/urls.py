from django.contrib import admin
from django.urls import include, path

from tests.test_app.views import Chat

urlpatterns = [
    path("chat/", Chat.as_view(), name="test"),
    path("admin/", admin.site.urls),
    path("api/", include("df_api_drf.urls")),
]
