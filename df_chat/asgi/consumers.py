import json
import typing

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.utils.serializer_helpers import ReturnDict

from df_chat.constants import (
    ROOM_CHAT_ALIAS,
    SYSTEM_CHAT_ALIAS,
    USER_CHAT_ALIAS,
)
from df_chat.drf.serializers import ChatMessageSerializer
from df_chat.models import MemberChannel


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(
        self, *args: tuple[typing.Any], **kwargs: dict[str, typing.Any]
    ) -> None:
        super().__init__(*args, **kwargs)
        self.user: typing.Any = None

    async def _unsubscribe_user_individual_room(self) -> None:
        await self.channel_layer.group_discard(
            USER_CHAT_ALIAS.format(user_id=self.user.id), self.channel_name
        )

    async def _subscribe_user_individual_room(self) -> None:
        await self.channel_layer.group_add(
            USER_CHAT_ALIAS.format(user_id=self.user.id), self.channel_name
        )

    @database_sync_to_async
    def get_user_group_ids(self) -> list[int]:
        return list(self.user.chatmember_set.values_list("chat_room", flat=True))

    async def _unsubscribe_chat_rooms(self) -> None:
        chat_membership_ids = await self.get_user_group_ids()
        for room_pk in chat_membership_ids:
            await self.channel_layer.group_discard(
                ROOM_CHAT_ALIAS.format(room_id=room_pk), self.channel_name
            )

    async def _subscribe_chat_rooms(self) -> None:
        chat_membership_ids = await self.get_user_group_ids()
        for room_pk in chat_membership_ids:
            await self.channel_layer.group_add(
                ROOM_CHAT_ALIAS.format(room_id=room_pk), self.channel_name
            )

    async def _unsubscribe_system_room(self) -> None:
        await self.channel_layer.group_discard(SYSTEM_CHAT_ALIAS, self.channel_name)

    async def _subscribe_system_room(self) -> None:
        await self.channel_layer.group_add(SYSTEM_CHAT_ALIAS, self.channel_name)

    async def subscribe(self) -> None:
        await self._subscribe_system_room()
        await self._subscribe_user_individual_room()
        await self._subscribe_chat_rooms()

    async def unsubscribe(self) -> None:
        await self._unsubscribe_system_room()
        await self._unsubscribe_user_individual_room()
        await self._unsubscribe_chat_rooms()

    async def connect(self) -> None:
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        await self.accept()
        await self.set_member_channel(is_online=True)
        await self.subscribe()

    async def disconnect(self) -> None:
        await self.unsubscribe()
        await self.set_member_channel(is_online=False)

    async def receive(self, text_data: str) -> None:
        text_data_json = json.loads(text_data)
        if text_data_json.get("type") == "chat.message.new":
            await self.store_message_to_db(text_data_json)

    async def chat_message_new(self, event: dict) -> None:
        await self.send(text_data=json.dumps(event))

    async def chat_message_update(self, event: dict) -> None:
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def store_message_to_db(self, event: dict) -> typing.Optional[ReturnDict]:
        serializer = ChatMessageSerializer(
            data={
                "message": event.get("message", ""),
            }
        )
        if serializer.is_valid():
            serializer.save(
                created_by_id=self.user.id, chat_room_id=event.get("chat_room")
            )

    @database_sync_to_async
    def set_member_channel(self, is_online: bool) -> None:
        if is_online:
            MemberChannel.objects.create(user=self.user, channel_name=self.channel_name)
        else:
            MemberChannel.objects.filter(channel_name=self.channel_name).delete()
