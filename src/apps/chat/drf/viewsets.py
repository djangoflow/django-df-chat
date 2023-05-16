from core.drf.permissions import IsOwnerOrReadOnly
from core.drf.serializers import ErrorResponseSerializer
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, permissions, response, serializers, status,\
    generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import Message, MessageImage, Room, RoomUser, Category
from .serializers import (
    MessageImageSerializer,
    MessageSeenSerializer,
    MessageSerializer,
    RoomSerializer,
    RoomUserSerializer,
    UserNameSerializer,
    CategorySerializer,
)


class CategoriesView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)


class RoomsByCategoryView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        category = Category.objects.get(id=category_id)

        return Room.objects.filter(category=category)


class RoomViewSet(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = RoomSerializer
    queryset = Room.objects.all().select_related("creator").order_by("-created")

    @action(
        methods=["post"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=serializers.Serializer,
    )
    def mute(self, request, *args, room_pk=None, **kwargs):
        return self._mute_unmute(request, *args, mute=True, **kwargs)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=serializers.Serializer,
    )
    def unmute(self, request, *args, room_pk=None, **kwargs):
        return self._mute_unmute(request, *args, mute=False, **kwargs)

    def _mute_unmute(self, request, *args, mute=True, **kwargs):
        room = self.get_object()
        if mute:
            room.muted_by.add(self.request.user)
        else:
            room.muted_by.remove(self.request.user)

        return response.Response(status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance.admins.add(self.request.user)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter_for_user(self.request.user)
            .annotate_message_count(self.request.user)
            .annotate_is_muted(self.request.user)
            .distinct()
        )


class RoomRelatedMixin:
    def get_room(self):
        return get_object_or_404(
            Room.objects.filter_for_user(self.request.user), pk=self.kwargs["room_pk"]
        )


class RoomUserViewSet(RoomRelatedMixin, ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = RoomUserSerializer
    pagination_class = None
    queryset = RoomUser.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(room=self.get_room())

    @extend_schema(responses={200: UserNameSerializer(many=True)})
    @action(methods=["get"], detail=False, serializer_class=UserNameSerializer)
    def names(self, *args, **kwargs):
        room = self.get_room()
        serializer = self.get_serializer_class()(data=room.users.all(), many=True)
        serializer.is_valid()
        return Response(serializer.data)


class MessageViewSet(RoomRelatedMixin, ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = MessageSerializer
    queryset = Message.objects.prefetch_children().distinct()

    @action(
        methods=["post"],
        detail=False,
        # TODO(eugapx): change permission class to RoomPermissions check the room_pk in kwargs (not critical)
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=MessageSeenSerializer,
    )
    def seen(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @extend_schema(responses={204: None, 400: ErrorResponseSerializer})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(room_user__room=self.get_room())
            .select_related("room_user", "room_user__user")
            .annotate_is_seen_by_me(self.request.user)
        )

        if self.action == "list":
            queryset = queryset.filter(is_reaction=False)

        return queryset


class MessageImageViewSet(ModelViewSet):
    serializer_class = MessageImageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = MessageImage.objects.all()
    parser_classes = (parsers.MultiPartParser,)

    def get_queryset(self):
        return self.queryset.filter(message__room_user__user=self.request.user)
