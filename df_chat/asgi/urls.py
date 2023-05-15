from . import consumers
from django.urls import re_path


urlpatterns = [
    re_path(r"(?P<room_id>\w+)/$", consumers.RoomConsumer.as_asgi()),
]
