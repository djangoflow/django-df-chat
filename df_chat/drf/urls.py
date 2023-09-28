from rest_framework.routers import DefaultRouter

from .viewsets import (
    ChatMediaViewSet,
    ChatMessageReactionsViewSet,
    ChatMessageViewSet,
    ChatRoomViewSet,
    RoomUserViewSet,
)

router = DefaultRouter()

router.register("room", ChatRoomViewSet, basename="chat_room")
router.register("user", RoomUserViewSet, basename="room_user")
router.register("message", ChatMessageViewSet, basename="chat_message")
router.register("media", ChatMediaViewSet, basename="chat_media")
router.register(
    "message_reactions", ChatMessageReactionsViewSet, basename="chat_message_reactions"
)

urlpatterns = router.urls
