import hashlib
from typing import TypeVar

from django.db import transaction
from django.db.models import Model

from df_chat.models import (
    ChatPermission,
    ChatRoom,
    RoomUser,
    RoomUserPermission,
)

PRIVATE_ROOM_PERMISSIONS = [
    ChatPermission.can_create_messages,
    ChatPermission.can_delete_own_messages,
    ChatPermission.can_edit_own_messages,
    ChatPermission.can_delete_room,
]

M = TypeVar("M", bound=Model)


def private_message_room_name(users: list[M]) -> str:
    user_ids = sorted([user.id for user in users])
    name_str = "private_messages_" + "_".join([str(user_id) for user_id in user_ids])
    return hashlib.sha256(name_str.encode("utf-8")).hexdigest()


def get_or_create_private_message_room(users: list[M]) -> ChatRoom:
    room_name = private_message_room_name(users)
    with transaction.atomic():
        room, created = ChatRoom.objects.get_or_create(
            name=room_name,
            type=ChatRoom.Type.PRIVATE_MESSAGES,
        )
        if created:
            for user in users:
                user = RoomUser.objects.create(
                    room=room,
                    user=user,
                )
                for permission in PRIVATE_ROOM_PERMISSIONS:
                    RoomUserPermission.objects.create(
                        room_user=user,
                        permission=permission,
                    )
    return room


...
