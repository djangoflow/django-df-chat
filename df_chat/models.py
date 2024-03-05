from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel


class ChatRoom(TimeStampedModel):
    class ChatType(models.TextChoices):
        group = "group", _("Group Chat")
        private = "private", _("Private Chat")

    title = models.CharField(max_length=128)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="df_chat.ChatMember"
    )
    chat_type = models.CharField(
        max_length=30, choices=ChatType.choices, default=ChatType.private
    )

    def __str__(self) -> str:
        return self.title

    @property
    def is_personal_chat(self) -> bool:
        return self.chat_type == "private"


class MemberChannelQuerySet(models.QuerySet):
    def subscribed_channels(self, user_id: int) -> "models.QuerySet[MemberChannel]":
        return self.filter(user_id=user_id)


class MemberChannel(TimeStampedModel):
    objects = MemberChannelQuerySet.as_manager()
    last_alive_at = models.DateTimeField(null=True, blank=True)
    channel_name = models.CharField(max_length=128, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.id}"


class ChatMember(TimeStampedModel):
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Room: {self.chat_room.id} - User {self.user.id}"


class MessageType(models.IntegerChoices):
    message = 0, _("Regular message")
    response = 1, _("Message response")
    reaction = 2, _("Reaction")


class ChatMessage(TimeStampedModel):
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(null=False, blank=False)
    message_type = models.IntegerField(
        choices=MessageType.choices, default=MessageType.message
    )
    parent = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE, related_name="children"
    )

    @property
    def reactions(self):
        """
        Return a queryset of reactions
        """
        return self.children.filter(
            message_type=MessageType.reaction,
        ).order_by("message")

    def __str__(self) -> str:
        return f"{self.created_by} >> {self.message}"

    class Meta:
        indexes = [
            models.Index(
                fields=["parent"],
                # Should work on Postgres but may not work on other DB engines.
                # Notably MariaDB/MySQL do not support conditional indexes, see
                # https://docs.djangoproject.com/en/5.0/ref/models/indexes/#condition
                # condition=models.Q(message_type=MessageType.reaction),
            ),
        ]
