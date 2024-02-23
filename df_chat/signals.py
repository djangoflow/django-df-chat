from typing import Any

from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from df_chat.models import ChatRoom
from df_chat.utils import DynamicUserGroupSubscriptionHandler


@receiver(m2m_changed, sender=ChatRoom.users.through)
def room_user_actions(
    instance: Any, action: str, pk_set: set, **kwargs: dict[str, Any]
) -> None:
    subscription_handler = DynamicUserGroupSubscriptionHandler()
    for user_id in pk_set:
        if action == "post_remove":
            subscription_handler.unsubscribe(user_id, instance.id)
        if action == "post_add":
            subscription_handler.subscribe(user_id, instance.id)
