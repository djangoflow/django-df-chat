from df_notifications.decorators import register_rule_model
from df_notifications.models import NotificationModelAsyncRule
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.db.models import Exists
from django.db.models import F
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models.manager import BaseManager
from django.db.models.signals import post_delete
from django.dispatch import receiver
from itertools import repeat
from model_utils.models import TimeStampedModel
from typing import List


User = get_user_model()


class RoomQuerySet(models.QuerySet):
    def filter_for_user(self, user):
        return self.filter(
            Q(is_public=True) | Q(users=user) | Q(admins=user) | Q(creator=user)
        ).distinct()

    def annotate_is_muted(self, user):
        return self.annotate(
            is_muted=Exists(
                Room.objects.filter(
                    muted_by=user,
                    id=OuterRef("id"),
                )
            )
        )

    def annotate_message_count(self, user=None):
        return self.annotate(
            message_total_count=Count("roomuser__message__id", distinct=True),
            message_read_count=Count(
                "roomuser__message__id",
                filter=Q(roomuser__message__seen_by=user),
                distinct=True,
            ),
            message_new_count=F("message_total_count") - F("message_read_count"),
        )


class Room(TimeStampedModel):
    def get_upload_to(self, filename):
        return f"images/room/{self.id}/{filename}"

    user_attribute = "creator"
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rooms_creator_set"
    )
    title = models.CharField(max_length=512)
    description = models.TextField(default="", blank=True)
    image = models.ImageField(upload_to=get_upload_to, null=True, blank=True)

    is_public = models.BooleanField(default=True)
    users = models.ManyToManyField(User, blank=True)
    admins = models.ManyToManyField(User, blank=True, related_name="rooms_admin_set")

    muted_by = models.ManyToManyField(User, blank=True, related_name="room_muted_set")

    objects = RoomQuerySet.as_manager()

    def __str__(self):
        return self.title

    class Meta:
        ordering = (
            "-modified",
            "title",
        )


class RoomUserManager(models.Manager):
    def get_room_user(self, room_pk, user_pk):
        room_user, _ = self.get_or_create(
            room_id=room_pk,
            user_id=user_pk,
            is_active=True,
        )
        if user_pk:
            room_user.room.users.add(user_pk)
            # Public rooms are muted by default
            if room_user.room.is_public:
                room_user.room.muted_by.add(user_pk)

        return room_user


class RoomUser(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Leave empty for a system message",
    )
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True)
    objects = RoomUserManager()

    def __str__(self):
        return f"{self.room}: {self.user}"


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


class MessageImage(TimeStampedModel):
    def get_upload_to(self, filename):
        return f"images/messages/{self.message.id}/{filename}"

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
        upload_to=get_upload_to, height_field="height", width_field="width"
    )
    width = models.IntegerField(default=500)
    height = models.IntegerField(default=300)

    def __str__(self):
        return self.image.url


@register_rule_model
class MessageNotificationRule(NotificationModelAsyncRule):
    model = Message

    def get_users(self, instance: Message) -> List[User]:
        return (
            User.objects.filter(
                roomuser__room=instance.room_user.room,
                roomuser__is_active=True,
                roomuser__is_online=False,
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


@receiver(post_delete, sender=Message)
def notify_delete_reaction(sender, instance, *args, **kwargs):
    if instance.parent:
        instance.parent.save()
