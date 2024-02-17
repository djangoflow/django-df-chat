from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework import mixins, permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from df_chat.drf.serializers import ChatRoomSerializer, UserSerializer, MemberIdsSerializer, \
    ChatMessageSerializer
from df_chat.models import ChatMessage, ChatRoom
from df_chat.paginators import RoomCursorPagination, ChatMessagePagination
from df_chat.permissions import IsChatRoomRelatedUser


User = get_user_model()


class RoomViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    pagination_class = RoomCursorPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        newest = ChatMessage.objects.filter(chat_group=OuterRef("pk")).order_by("-created_at")
        return ChatRoom.objects.filter(
            users=self.request.user
        ).annotate(newest_message=Subquery(newest.values("message")[:1]))

    @extend_schema(request=ChatMessageSerializer, responses={200: OpenApiResponse(response=ChatMessageSerializer(many=False))})
    @action(
        detail=True,
        methods=['POST', ],
        url_path='message',
    )
    def message(self, request, pk=None, **kwargs):
        data_to_store = {
            **request.data,
            "sender": self.request.user.id,
            "chat_group": pk
        }
        serializer = ChatMessageSerializer(data=data_to_store)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_group_{pk}",
            {"type": "chat.post.message", **serializer.data}
        )
        return Response(serializer.data, status=200)

    @extend_schema(responses={200: OpenApiResponse(response=UserSerializer(many=True))})
    @action(
        detail=True,
        methods=['GET', ],
        pagination_class=None,
        url_path='members',
    )
    def members(self, request, pk=None, **kwargs):
        chat_members = User.objects.filter(chat_membership__chat_group=pk)
        serializer = UserSerializer(chat_members, many=True)
        return Response(serializer.data, status=200)

    @extend_schema(request=MemberIdsSerializer, responses={
        200: OpenApiResponse(response=None, description='Successfully added user to a group'),
        406: OpenApiResponse(
            response=None,
            description='Not allowed error message for a private chat when we trying to add more than 2 users')
    })
    @members.mapping.post
    def post_members(self, request, pk=None, **kwargs):
        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        users = User.objects.filter(pk__in=serializer.validated_data.get("user_ids"))
        if len(users) == 0:
            return Response(status=status.HTTP_200_OK)

        chat_room = ChatRoom.objects.get(id=pk)

        match serializer.validated_data.get(MemberIdsSerializer.ACTION):
            case MemberIdsSerializer.ACTION_ADD:
                if chat_room.is_personal_chat and chat_room.users.count() <= 1:
                    chat_room.users.add(users[0])
                elif not chat_room.is_personal_chat:
                    chat_room.users.add(*users)
                else:
                    return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
            case MemberIdsSerializer.ACTION_REMOVE:
                chat_room.users.remove(*users)
        return Response(status=status.HTTP_200_OK)


class MessagesList(ListAPIView):
    serializer_class = ChatMessageSerializer
    pagination_class = ChatMessagePagination
    permission_classes = (permissions.IsAuthenticated, IsChatRoomRelatedUser)

    def get_queryset(self):
        group_pk = self.kwargs['group_pk']
        return ChatMessage.objects.filter(chat_group=group_pk)

    def get(self, request, *args, **kwargs):
        group = ChatRoom.objects.prefetch_related("users").filter(id=self.kwargs['group_pk']).first()
        self.check_object_permissions(self.request, group)
        return super(MessagesList, self).get(request, *args, **kwargs)
