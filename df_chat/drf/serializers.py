from typing import Any, Dict

from rest_framework import serializers

from df_chat.models import ChatMessage, ChatMessageReaction, ChatRoom, RoomUser
from df_chat.utils import get_chat_user_model

ChatUser = get_chat_user_model()


class ChatRoomSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=ChatUser.objects.all(), allow_null=True
    )

    class Meta:
        model = ChatRoom
        fields = "__all__"

    def validate(self, attrs: Dict[str, Any]) -> Dict:
        user = self.context["request"].user
        if attrs["type"] == ChatRoom.Type.PRIVATE_MESSAGES and not attrs["user"]:
            raise serializers.ValidationError(
                "User required for creating private message room"
            )
        if (
            attrs["type"] == ChatRoom.Type.PRIVATE_MESSAGES
            and RoomUser.objects.filter(
                create_by=user.chat_user,
                room__type=ChatRoom.Type.PRIVATE_MESSAGES,
                user=attrs["user"],
            ).exists()
        ):
            raise serializers.ValidationError("Room already exists...")
        return attrs


class RoomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomUser
        fields = "__all__"


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"


class ChatMessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessageReaction
        fields = "__all__"
