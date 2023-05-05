from django.urls import re_path

from . import consumers

urlpatterns = [
    re_path(r"(?P<room_id>\w+)/$", consumers.RoomConsumer.as_asgi()),
]
