from .viewsets import MessageImageViewSet
from .viewsets import MessageViewSet
from .viewsets import RoomUserViewSet
from .viewsets import RoomViewSet
from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers


if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()


router.register("rooms", RoomViewSet, basename="rooms")
router.register("images", MessageImageViewSet, basename="images")

urlpatterns = router.urls

rooms_router = routers.NestedSimpleRouter(router, "rooms", lookup="room")
rooms_router.register("users", RoomUserViewSet, basename="rooms-users")
rooms_router.register("messages", MessageViewSet, basename="rooms-messages")
urlpatterns = router.urls + rooms_router.urls
