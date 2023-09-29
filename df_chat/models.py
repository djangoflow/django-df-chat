import typing

from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from .settings import api_settings

M = typing.Type[models.Model]


class ChatRoomAvatar(TimeStampedModel):
    file = models.ImageField(upload_to="chat_room_avatars")


class ChatRoom(TimeStampedModel):
    class Type(models.TextChoices):
        PRIVATE_MESSAGES = "private_messages", "Private messages"
        GROUP = "group", "Group"
        CHANNEL = "channel", "Channel"

    type = models.CharField(
        max_length=255,
        choices=Type.choices,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(default="")
    chat_room_avatar = models.ForeignKey(
        ChatRoomAvatar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Does appear in search results; can be joined by anyone",
    )


class ChatPermission(models.TextChoices):
    can_add_users = "can_add_users"
    can_remove_users = "can_remove_users"
    can_create_messages = "can_create_messages"
    can_delete_messages = "can_delete_messages"
    can_delete_own_messages = "can_delete_own_messages"
    can_edit_messages = "can_edit_messages"
    can_edit_own_messages = "can_edit_own_messages"
    can_edit_room = "can_edit_room"
    can_delete_room = "can_delete_room"


class RoomUser(TimeStampedModel):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(api_settings.CHAT_USER_MODEL, on_delete=models.CASCADE)
    muted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        api_settings.CHAT_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )
    last_seen_at = models.DateTimeField(
        default=timezone.now,
        help_text="We use this fields to show how many messages are unread",
    )


class RoomUserPermission(TimeStampedModel):
    room_user = models.ForeignKey(RoomUser, on_delete=models.CASCADE)
    permission = models.CharField(max_length=255, choices=ChatPermission.choices)


class ChatMessage(TimeStampedModel):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(api_settings.CHAT_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(default="")
    edited_at = models.DateTimeField(null=True, blank=True)
    in_reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Use for replies and sharing messages. Sharing a message is like a reply, but with other room.",
    )


class ChatFile(TimeStampedModel):
    file = models.FileField(upload_to="chat_files")


class ChatMessageFile(TimeStampedModel):
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="files"
    )
    file = models.ForeignKey(ChatFile, on_delete=models.CASCADE, related_name="+")
    sequence = models.IntegerField(default=0)


class ChatMessageReaction(TimeStampedModel):
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(api_settings.CHAT_USER_MODEL, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=255)
