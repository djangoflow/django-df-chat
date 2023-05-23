from . import consumers
from django.urls import re_path


urlpatterns = [
    re_path("", consumers.RoomsConsumer.as_asgi()),
]
