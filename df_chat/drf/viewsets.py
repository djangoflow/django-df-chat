from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Max, OuterRef, QuerySet, Subquery
from rest_framework import mixins, permissions, status
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from df_chat.drf.serializers import (
    ChatMessageSerializer,
    ChatMessageUpdateSerializer,
    ChatRoomMembersSerializer,
    ChatRoomSerializer,
    UserSerializer,
)
from df_chat.models import ChatMessage, ChatRoom
from df_chat.paginators import ChatMessagePagination, ChatRoomPagination

User = get_user_model()


class MessageViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    pagination_class = ChatMessagePagination
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[ChatMessage]:
        return ChatMessage.objects.filter(chat_room=self.kwargs.get("room_id"))

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_serializer_class(
        self,
    ) -> Any:
        serializer_class = self.serializer_class
        if self.request.method in ["PATCH", "PUT"]:
            serializer_class = ChatMessageUpdateSerializer
        return serializer_class


class RoomViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomSerializer
    pagination_class = ChatRoomPagination

    def get_queryset(self) -> "QuerySet[ChatRoom]":
        newest = ChatMessage.objects.filter(chat_room=OuterRef("pk")).order_by(
            "-created"
        )
        return ChatRoom.objects.filter(users=self.request.user).annotate(
            newest_message=Subquery(newest.values("message")[:1]),
            last_message_id=Max("chatmessage__id"),
        )

    @action(
        detail=True,
        methods=["POST"],
        serializer_class=ChatRoomMembersSerializer,
        pagination_class=None,
        url_path="member",
    )
    def member(self, request: Request, **kwargs: dict[str, Any]) -> Response:
        instance = self.get_object()
        serializer = ChatRoomMembersSerializer(
            data=request.data, context={"request": request, "instance": instance}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["GET"],
        serializer_class=UserSerializer,
        pagination_class=None,
    )
    def members(self, request: Request, **kwargs) -> Response:
        instance = self.get_object()
        serializer = UserSerializer(
            instance.users.all(), many=True, context={"request": request}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)
