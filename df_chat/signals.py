from df_chat.models import Message
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=Message)
def notify_delete_reaction(sender, instance, *args, **kwargs):
    if instance.parent:
        instance.parent.save()
