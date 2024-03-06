from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from df_chat.models import ChatMember, ChatMessage, ChatRoom, MessageType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
        ]


class ChatMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "created",
            "modified",
            "message",
            "chat_room",
            "created_by",
            "message_type",
            "parent",
        )
        read_only_fields = (
            "id",
            "created",
            "modified",
            "chat_room",
            "created_by",
            "message_type",
            "parent",
        )


class ChatMessageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
        required=False,
    )
    chat_room = serializers.PrimaryKeyRelatedField(
        queryset=ChatRoom.objects.all(), many=False, required=False
    )
    reactions = serializers.SerializerMethodField("get_reactions")
    replies = serializers.SerializerMethodField("get_replies")

    def to_internal_value(self, raw_data: dict) -> dict:
        data = super().to_internal_value(raw_data)
        view = self.context.get("view")
        if data["chat_room"] is None and view and view.kwargs.get("room_id"):
            data["chat_room"] = ChatRoom.objects.get(id=view.kwargs.get("room_id"))
        return data

    def validate(self, data: dict) -> dict:
        """
        Check that only allowed reactions make it through!
        """
        message_type = data["message_type"]
        reaction = data["message"]
        allowed = getattr(settings, "DF_CHAT_ALLOWED_REACTIONS", ())

        if message_type == MessageType.reaction and allowed and reaction not in allowed:
            raise serializers.ValidationError(f"Invalid reaction '{reaction}'")
        return data

    def get_reactions(self, message):
        """
        Transform the response into a different format,
        groupped by the actual reaction message.
        """
        response = []
        previous_message = None
        current_chunk = None

        for reaction in message.reactions.values():
            if reaction["message"] != previous_message:
                if current_chunk:
                    response.append(current_chunk)

                current_chunk = {
                    "content": reaction["message"],
                    "reactions": [reaction],
                }
            else:
                current_chunk["reactions"].append(reaction)

            previous_message = reaction["message"]

        # append if anything that's left at the end
        if current_chunk:
            response.append(current_chunk)

        return response

    def get_replies(self, message):
        return message.replies.values() or []

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "chat_room",
            "created_by",
            "message",
            "created",
            "message_type",
            "parent",
            "reactions",
            "replies",
        )


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
