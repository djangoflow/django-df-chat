from django.urls import path, include
from rest_framework.routers import DefaultRouter

from df_chat.drf.viewsets import RoomViewSet, MessagesList

router = DefaultRouter()

router.register("room", RoomViewSet, basename="room")
urlpatterns = [
    path('messages/<int:group_pk>', MessagesList.as_view()),
    *router.urls
]
