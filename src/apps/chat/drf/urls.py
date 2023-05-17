from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_nested import routers

from .viewsets import (
    MessageImageViewSet,
    MessageViewSet,
    RoomUserViewSet,
    RoomViewSet,
    CategoriesViewSet,
)


if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()


router.register("rooms", RoomViewSet, basename="rooms")
router.register("images", MessageImageViewSet, basename="images")
router.register("categories", CategoriesViewSet, basename="categories")


rooms_router = routers.NestedSimpleRouter(router, "rooms", lookup="room")
rooms_router.register("users", RoomUserViewSet, basename="rooms-users")
rooms_router.register("messages", MessageViewSet, basename="rooms-messages")


urlpatterns = router.urls + rooms_router.urls