from ..models import Message
from ..models import MessageImage
from ..models import Room
from ..models import RoomUser
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from hashid_field.rest import HashidSerializerCharField
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.relations import ManyRelatedField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework_recursive.fields import RecursiveField
from typing import Optional


User = get_user_model()


class ErrorSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
    field = serializers.CharField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    errors = ErrorSerializer(many=True, required=True)


class MessageSeenSerializer(serializers.Serializer):
    message_ids = serializers.ListSerializer(child=serializers.CharField())

    def save(self, **kwargs):
        user = self.context["request"].user
        messages = Message.objects.filter(
            Q(pk__in=self.validated_data["message_ids"])
            & (
                Q(room_user__room__is_public=True)
                | Q(room_user__room__users=user)
                | Q(room_user__room__admins=user)
            )
        )
        message_ids = []
        for message in messages:
            message.seen_by.add(user)
            message_ids.append(str(message.pk))
        setattr(self, "_data", {"message_ids": message_ids})


class CreatorMixin:
    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs["creator"] = self.context["request"].user
        return attrs


class MessageImageSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True)
    message_id = HashidSerializerCharField(
        source_field="df_chat.MessageImage.id", required=False
    )
    room_id = HashidSerializerCharField(source_field="df_chat.Room.id", required=False)
    name = serializers.SerializerMethodField()

    class Meta:
        model = MessageImage
        read_only_fields = (
            "height",
            "width",
            "name",
        )
        fields = ("id", "message_id", "room_id", "image", *read_only_fields)

    def get_name(self, obj) -> str:
        return obj.image.name.split("/")[-1]

    def validate_message_id(self, message_id):
        try:
            Message.objects.get(
                pk=message_id, room_user__user=self.context.get("request").user
            )
        except Message.DoesNotExist:
            raise exceptions.ValidationError(
                "You can only attach images to your own messages"
            )
        return message_id

    def validate(self, attrs):
        room_id = attrs.pop("room_id", None)
        if room_id and not attrs.get("message_id"):
            attrs["message_id"] = str(
                Message.objects.create(
                    room_user=RoomUser.objects.get_room_user(
                        room_pk=room_id,
                        user_pk=self.context["request"].user.id,
                    )
                ).id
            )
        return super().validate(attrs)


class MessageSerializer(serializers.ModelSerializer):
    def get_is_me(self, obj) -> Optional[bool]:
        if self.context.get("request"):
            return self.context["request"].user.id == obj.room_user.user_id

        # In case of ws we will resolve user_id -> is_me later
        return str(obj.room_user_id)

    id = HashidSerializerCharField(read_only=True)
    parent_id = HashidSerializerCharField(
        source_field="df_chat.Message.id", required=False
    )
    room_user_id = HashidSerializerCharField(read_only=True)
    room_id = HashidSerializerCharField(source="room_user.room_id", read_only=True)
    is_me = serializers.SerializerMethodField()
    is_seen_by_me = serializers.BooleanField(read_only=True)
    is_reaction = serializers.BooleanField(default=False)
    images = MessageImageSerializer(many=True, read_only=True)
    reactions = serializers.ListSerializer(child=RecursiveField(), read_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        attrs["room_user"] = RoomUser.objects.get_room_user(
            room_pk=self.context["view"].get_room().pk,
            user_pk=self.context["request"].user.id,
        )
        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.is_reaction and instance.parent:
            # Trigger message post_save signal
            instance.parent.save()
        return instance

    class Meta:
        model = Message
        read_only_fields = (
            "id",
            "created",
            "modified",
            "room_user_id",
            "is_me",
            "is_seen_by_me",
            "room_id",
            "images",
            "reactions",
        )
        fields = read_only_fields + ("body", "parent_id", "is_reaction")


class HashidCharPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    def to_representation(self, value):
        return str(value.pk)


class RoomSerializer(CreatorMixin, serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True)
    creator_id = HashidSerializerCharField(read_only=True)
    message_total_count = serializers.IntegerField(read_only=True)
    message_new_count = serializers.IntegerField(read_only=True)
    users = ManyRelatedField(
        child_relation=HashidCharPrimaryKeyRelatedField(
            queryset=User.objects.all(), required=False
        ),
        required=False,
    )
    last_message = serializers.SerializerMethodField()
    is_muted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Room
        read_only_fields = (
            "id",
            "created",
            "modified",
            "creator_id",
            "message_total_count",
            "message_new_count",
            "last_message",
            "is_muted",
        )
        fields = read_only_fields + (
            "title",
            "description",
            "is_public",
            "image",
            "users",
        )

    @extend_schema_field(MessageSerializer(allow_null=True))
    def get_last_message(self, obj):
        return MessageSerializer(
            Message.objects.filter(room_user__room=obj).order_by("-created").first(),
            context=self.context,
        ).data

    def get_is_muted(self, obj: Room) -> bool:
        return obj.muted_by.all()


class RoomUserSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True)

    def get_is_me(self, obj) -> Optional[bool]:
        if self.context.get("request"):
            return self.context["request"].user.id == obj.user_id

        # In case of ws we will resolve user_id -> is_me later
        return str(obj.id)

    name = serializers.CharField(read_only=True, source="avatar.slug")
    image = serializers.ImageField(read_only=True, source="avatar.image")
    is_me = serializers.SerializerMethodField()
    room_id = HashidSerializerCharField(read_only=True)
    is_online = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        model = RoomUser
        read_only_fields = (
            "id",
            "name",
            "image",
            "is_me",
            "is_online",
            "is_active",
            "room_id",
        )
        fields = read_only_fields


class UserNameSerializer(serializers.ModelSerializer):
    id = HashidSerializerCharField(read_only=True)

    class Meta:
        model = User
        read_only_fields = ("display_name",)
        fields = ("id", *read_only_fields)
