from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.db.models import Exists
from django.db.models import F
from django.db.models import OuterRef
from django.db.models import Q
from model_utils.models import TimeStampedModel


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
