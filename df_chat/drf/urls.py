from .viewsets import MessageViewSet, RoomUserViewSet, RoomViewSet, MessageImageViewSet, RoomCategoryViewSet
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
router.register("categories", RoomCategoryViewSet, basename="room-categories")

urlpatterns = router.urls

rooms_router = routers.NestedSimpleRouter(router, "rooms", lookup="room")
rooms_router.register("users", RoomUserViewSet, basename="room-users")
rooms_router.register("messages", MessageViewSet, basename="room-messages")
urlpatterns = router.urls + rooms_router.urls
