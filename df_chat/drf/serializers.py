from rest_framework import serializers

from df_chat.models import ChatMessage, ChatMessageReaction, ChatRoom, RoomUser


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = "__all__"


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
