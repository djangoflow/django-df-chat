from django.urls import include, path
from rest_framework.routers import SimpleRouter

from df_chat.drf.viewsets import MessageViewSet, RoomViewSet

room_router = SimpleRouter()
messages_router = SimpleRouter()


room_router.register("rooms", RoomViewSet, basename="room")

messages_router.register("messages", MessageViewSet, basename="messages")
urlpatterns = [
    path("rooms/<int:room_id>/", include(messages_router.urls)),
    *room_router.urls,
]
