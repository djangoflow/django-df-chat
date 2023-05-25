from df_chat.models import RoomUser
from df_notifications.decorators import register_rule_model
from df_notifications.models import NotificationModelAsyncRule
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models.manager import BaseManager
from itertools import repeat
from model_utils.models import TimeStampedModel
from typing import List


User = get_user_model()


class MessageQuerySet(models.QuerySet):
    def prefetch_children(self):
        lookup = "__".join(repeat("children", 3))
        return self.prefetch_related("images", lookup)

    def annotate_is_seen_by_me(self, user=None):
        return self.annotate(
            is_seen_by_me=Exists(
                Message.objects.filter(seen_by=user, id=OuterRef("id"))
            )
        )


class MessageManager(BaseManager.from_queryset(MessageQuerySet)):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("room_user__user")


class Message(TimeStampedModel):
    user_attribute = "room_user.user"

    is_reaction = models.BooleanField(default=False)
    room_user = models.ForeignKey(RoomUser, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE, related_name="children"
    )
    body = models.TextField(default="")
    objects = MessageManager()

    # TODO(alexis): consider through a model to record timestamps when the message is seen / sent to implement
    # whatsapp like double checkmarks
    seen_by = models.ManyToManyField(User, blank=True, related_name="message_seen_set")
    received_by = models.ManyToManyField(
        User, blank=True, related_name="message_received_set"
    )

    def reactions(self):
        return [m for m in self.children.all() if m.is_reaction]

    def __str__(self):
        return f"{self.room_user.user.email if self.room_user.user else '__system___'}: {self.body}"

    class Meta:
        ordering = ("-created",)


@register_rule_model
class MessageNotificationRule(NotificationModelAsyncRule):
    model = Message

    def get_users(self, instance: Message) -> List[User]:
        return (
            User.objects.filter(
                roomuser__room=instance.room_user.room,
                roomuser__is_active=True,
                roomuser__user__user_chat__is_online=False,
            )
            .exclude(id=instance.room_user.user.id if instance.room_user.user else None)
            .exclude(id__in=instance.room_user.room.muted_by.values("id"))
            .distinct()
        )

    @classmethod
    def get_queryset(cls, instance, prev):
        if instance.room_user.user:
            return cls.objects.all()
        # Do not send notifications for system messages
        return cls.objects.none()
