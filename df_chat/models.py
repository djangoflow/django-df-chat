from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ChatRoom(models.Model):
    class ChatType(models.TextChoices):
        GROUP = "group", _("Group Chat")
        PRIVATE = "private", _("Private Chat")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_chats")
    modified_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=515)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ChatMembers')
    chat_type = models.CharField(
        max_length=30,
        null=False,
        blank=False,
        choices=ChatType,
        default=ChatType.PRIVATE
    )

    def __str__(self):
        return self.title

    @property
    def is_personal_chat(self):
        return self.chat_type == 'private'


class MemberStatus(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_member")
    is_online = models.BooleanField(default=False)
    channel_name = models.CharField(max_length=128, null=True, blank=True)


class ChatMembers(models.Model):
    joined_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # relations fields
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_membership")
    chat_group = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="chat_membership")


class ChatMessage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    chat_group = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        null=False,
        blank=False
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.sender} >> {self.message}"

    def save(self, *args, **kwargs):
        super(ChatMessage, self).save(*args, **kwargs)
