from rest_framework import serializers
from django.contrib.auth import get_user_model

from df_chat.constants import ROOM_CHAT_ALIAS
from df_chat.models import ChatMessage, ChatMembers, ChatRoom

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.CharField(source='chat_member.is_online', read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", 'is_online']





class ChatMembersSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChatMembers
        fields = (
            "joined_at",
            "user",
        )


class ChatMessageSerializer(serializers.ModelSerializer):
    ws_room_name = serializers.SerializerMethodField(read_only=True)
    sender = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
    )

    class Meta:
        model = ChatMessage
        fields = (
            'id',
            "chat_group",
            "sender",
            "message",
            "created_at",
            "ws_room_name"
        )

    def get_ws_room_name(self, instance):
        return ROOM_CHAT_ALIAS.format(room_id=instance.chat_group.id)

    def to_representation(self, instance):
        result = super(ChatMessageSerializer, self).to_representation(instance)
        if hasattr(instance, "type"):
            result = {"type": instance.type, **result}
        return result

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.type = "chat.message.new"
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.type = "chat.message.edit"
        return instance


class ChatRoomSerializer(serializers.ModelSerializer):
    newest_message = serializers.CharField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
    )
    class Meta:
        model = ChatRoom
        fields = (
            "id",
            "title",
            "created_at",
            "created_by",
            "chat_type",
            "newest_message",
        )



class MemberIdsSerializer(serializers.Serializer):
    ACTION = "action"
    ACTION_ADD = "add"
    ACTION_REMOVE = "remove"

    user_ids = serializers.ListField(
       child=serializers.IntegerField()
    )
    action = serializers.ChoiceField([ACTION_ADD, ACTION_REMOVE])
