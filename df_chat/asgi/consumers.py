import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from df_chat.constants import USER_CHAT_ALIAS, ROOM_CHAT_ALIAS, SYSTEM_CHAT_ALIAS
from df_chat.drf.serializers import ChatMessageSerializer
from df_chat.models import MemberChannel


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    async def _unsubscribe_user_individual_room(self):
        await self.channel_layer.group_discard(
            USER_CHAT_ALIAS.format(user_id=self.user.id), self.channel_name
        )

    async def _subscribe_user_individual_room(self):
        await self.channel_layer.group_add(
            USER_CHAT_ALIAS.format(user_id=self.user.id), self.channel_name
        )

    @database_sync_to_async
    def get_user_group_ids(self) -> list[int]:
        return list(self.user.chat_membership.values_list("chat_group", flat=True))

    async def _unsubscribe_chat_rooms(self):
        chat_membership_ids = await self.get_user_group_ids()
        for room_pk in chat_membership_ids:
            await self.channel_layer.group_discard(
                ROOM_CHAT_ALIAS.format(room_id=room_pk), self.channel_name
            )

    async def _subscribe_chat_rooms(self):
        chat_membership_ids = await self.get_user_group_ids()
        for room_pk in chat_membership_ids:
            await self.channel_layer.group_add(
                ROOM_CHAT_ALIAS.format(room_id=room_pk), self.channel_name
            )

    async def _unsubscribe_system_room(self):
        await self.channel_layer.group_discard(
            SYSTEM_CHAT_ALIAS, self.channel_name
        )

    async def _subscribe_system_room(self):
        await self.channel_layer.group_add(
            SYSTEM_CHAT_ALIAS, self.channel_name
        )

    async def subscribe(self):
        await self._subscribe_system_room()
        await self._subscribe_user_individual_room()
        await self._subscribe_chat_rooms()

    async def unsubscribe(self):
        await self._unsubscribe_system_room()
        await self._unsubscribe_user_individual_room()
        await self._unsubscribe_chat_rooms()

    async def connect(self):
        self.user = self.scope["user"]
        await self.accept()
        await self.set_member_channel(is_online=True)
        await self.subscribe()

    async def disconnect(self, close_code):
        await self.unsubscribe()
        await self.set_member_channel(is_online=False)

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        ws_room_name = None
        data = None
        match text_data_json.get("type"):
            case "chat.message.new":
                ws_room_name, data = await self.store_message_to_db(text_data_json)
            case "chat.message.edit":
                pass
            case "chat.members.list":
                ws_room_name, data = 1, 1
        if ws_room_name and data:
            await self.channel_layer.group_send(
                ws_room_name, data
            )

    async def chat_message_new(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_post_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_get_members(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_get_groups(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def store_message_to_db(self, event: dict):
        serializer = ChatMessageSerializer(
            data={
                'chat_group': event.get('chat_group'),
                'sender': self.user.id,
                'message': event.get('message', '')
            }
        )
        if serializer.is_valid():
            serializer.save()
            return serializer.data.get('ws_room_name'), serializer.data
        return None, None

    @database_sync_to_async
    def set_member_channel(self, is_online: bool) -> None:
        if is_online:
            MemberChannel.objects.create(
                user=self.user, channel_name=self.channel_name
            )
        else:
            MemberChannel.objects.filter(channel_name=self.channel_name).delete()
