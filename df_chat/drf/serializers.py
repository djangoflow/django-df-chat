from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from df_chat.constants import ROOM_CHAT_ALIAS
from df_chat.models import ChatMember, ChatMessage, ChatRoom
from df_chat.settings import api_settings

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = api_settings.DEFAULT_USER_SERIALIZER_FIELDS


class ChatMessageSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "created",
            "modified",
            "chat_room",
            "created_by",
            "message",
        )
        read_only_fields = (
            "id",
            "created",
            "modified",
            "chat_room",
            "created_by",
        )

    def _post_to_ws(self, instance, message_type, **kwargs):
        channel_layer = get_channel_layer()
        ws_room_name = ROOM_CHAT_ALIAS.format(room_id=instance.chat_room.id)
        message_data = ChatMessageSerializer(instance=instance).data
        async_to_sync(channel_layer.group_send)(
            ws_room_name, {"type": message_type, **message_data}
        )

    def create(self, validated_data):
        instance = super().create(validated_data)
        self._post_to_ws(instance, "chat.message.new")
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._post_to_ws(instance, "chat.message.update")
        return instance


class ChatRoomSerializer(serializers.ModelSerializer):
    newest_message = serializers.CharField(read_only=True)
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, many=True
    )

    class Meta:
        model = ChatRoom
        fields = ("id", "title", "created", "chat_type", "newest_message", "users")
        read_only_fields = (
            "id",
            "created",
            "newest_message",
        )

    def validate(self, data: dict) -> dict:
        chat_type = data["chat_type"]
        users = data["users"]
        if ChatRoom.ChatType.private.value == chat_type and len(users) != 2:
            raise serializers.ValidationError(
                "Only 2 users are allowed at private chat"
            )
        return data

    def create(self, validated_data: dict) -> ChatRoom:
        instance = super().create(validated_data)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            ChatMember.objects.filter(user=request.user, chat_room=instance).update(
                is_owner=True
            )
        return instance


class ChatRoomMemberListSerializer(serializers.ModelSerializer):
    members = UserSerializer(source="users", many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ("members",)


class ChatRoomMembersSerializer(serializers.Serializer):
    class Action:
        add = "add"
        remove = "remove"

    users = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    action = serializers.ChoiceField([Action.add, Action.remove])

    class Meta:
        fields = ("users", "action")

    def validate(self, data: dict) -> dict:
        instance = self.context["instance"]
        if ChatRoom.ChatType.private.value == instance.chat_type:
            raise serializers.ValidationError("Impossible to add or remove user")
        return data

    def update(self) -> None:
        instance = self.context["instance"]
        users = self.validated_data["users"]
        if self.validated_data.get("action") == ChatRoomMembersSerializer.Action.add:
            instance.users.add(*users)
        if self.validated_data.get("action") == ChatRoomMembersSerializer.Action.remove:
            instance.users.remove(*users)
