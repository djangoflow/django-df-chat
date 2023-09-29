from typing import Type, Union

from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured

from df_chat.models import (
    ChatPermission,
    M,
)
from df_chat.settings import api_settings

PRIVATE_ROOM_PERMISSIONS = [
    ChatPermission.can_create_messages,
    ChatPermission.can_delete_own_messages,
    ChatPermission.can_edit_own_messages,
    ChatPermission.can_delete_room,
]


# def private_message_room_name(users: list[ChatUser]) -> str:
#     user_ids = sorted([user.id for user in users])
#     name_str = "private_messages_" + "_".join([str(user_id) for user_id in user_ids])
#     return hashlib.sha256(name_str.encode("utf-8")).hexdigest()
#
#
# def get_or_create_private_message_room(users: list[]) -> ChatRoom:
#     room_name = private_message_room_name(users)
#     with transaction.atomic():
#         room, created = ChatRoom.objects.get_or_create(
#             name=room_name,
#             type=ChatRoom.Type.PRIVATE_MESSAGES,
#         )
#         if created:
#             for user in users:
#                 user = RoomUser.objects.create(
#                     room=room,
#                     user=user,
#                 )
#                 for permission in PRIVATE_ROOM_PERMISSIONS:
#                     RoomUserPermission.objects.create(
#                         room_user=user,
#                         permission=permission,
#                     )
#     return room


def get_chat_user_model() -> Type[Union[M, M]]:
    """
    Return the User model that is active in this project.
    """
    try:
        return django_apps.get_model(api_settings.CHAT_USER_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "CHAT_USER_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "CHAT_USER_MODEL refers to model '%s' that has not been installed"
            % api_settings.CHAT_USER_MODEL
        )
