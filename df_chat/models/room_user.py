from df_chat.models import Room
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class RoomUserManager(models.Manager):
    def get_room_user(self, room_pk, user_pk):
        room_user, _ = self.get_or_create(
            room_id=room_pk,
            user_id=user_pk,
            is_active=True,
        )
        if user_pk:
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

    objects = RoomUserManager()

    @property
    def is_online(self):
        """
        A RoomUser could be an actual user or a system.
        Here, we infer that a user is online only if they have a UserChat associated with them.
        """
        return (
            self.user
            and hasattr(self.user, "user_chat")
            and self.user.user_chat.is_online
        )

    def __str__(self):
        return f"{self.room}: {self.user}"
