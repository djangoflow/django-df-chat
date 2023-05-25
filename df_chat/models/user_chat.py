from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class UserChatManager(models.Manager):
    def get_user_chat(self, user_pk: int) -> "UserChat":
        """
        In order to use the chat application, a user must be associated with a UserChat object.
        However, we do not want to create a UserChat object for every user that is added to the system.
        Instead, we only want to create a UserChat object when the user is connected to our chat application.
        """
        user_chat, _ = self.get_or_create(user_id=user_pk)
        return user_chat


class UserChat(models.Model):
    """
    This model stores attributes that should be visible across all rooms for a user.
    For example, if a user is online, we set the 'is_online' flag on this model for that user,
    which will then be visible to all the rooms that the user is a part of.
    """

    user = models.OneToOneField(
        User, related_name="user_chat", on_delete=models.CASCADE
    )
    is_online = models.BooleanField(default=False)

    objects = UserChatManager()

    def __str__(self):
        return self.user.__str__()
