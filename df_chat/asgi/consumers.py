from channels.db import database_sync_to_async
from df_chat.drf.serializers import MessageSerializer
from df_chat.drf.serializers import RoomSerializer
from df_chat.drf.serializers import RoomUserSerializer
from df_chat.models import Message
from df_chat.models import Room
from df_chat.models import RoomUser
from df_chat.models import UserChat
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer import ModelObserver


def post_init_receiver(self, instance, **kwargs):
    self.get_observer_state(instance).current_groups = set()


ModelObserver.post_init_receiver = post_init_receiver


class RoomsConsumer(GenericAsyncAPIConsumer):
    """
    A websocket consumer to allow users to listen to all activities in rooms.

    Once connected to the websocket, we automatically subscribe to all the rooms, the user is part of.
    So, the user will be able to listen to activities across his rooms, without having to use multiple connections.
    """

    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    user = None

    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.user_connect()
        await self.subscribe_to_rooms_activities()
        # TODO(eugapx) subscribe to group for this room only instead of one global group
        # so that when you broadcast messages you broarcast them only to the consumers in one room
        # instead of broadcasting all messages to all consumers
        # so that peeople in private group can't hack messages in private group that they receive

        await self.accept()

    async def disconnect(self, close_code):
        # When the user disconnects, we should unsubscribe them from listening to all activities.
        await self.unsubscribe_from_all_activities()
        await self.user_disconnect()

    @model_observer(RoomUser, serializer_class=RoomUserSerializer)
    async def room_user_activity(self, message: dict, **kwargs):
        self._resolve_is_me(message)
        await self.send_json(
            {
                "messages": [],
                "users": [message],
            }
        )

        if message["is_me"] and not message["is_active"]:
            # Create new room_user if old one was inactivated
            await self.user_connect()

    @room_user_activity.groups_for_signal
    def room_user_activity(self, instance: RoomUser, **kwargs):
        yield f"-room__{instance.room_id}"

    @room_user_activity.groups_for_consumer
    def room_user_activity(self, consumer, room_pk: str):
        yield f"-room__{room_pk}"

    @database_sync_to_async
    def get_rooms(self):
        rooms = self.user.room_set.all()
        # ensure that RoomUser objects are created for the user, for all the Rooms he is part of.
        for room in rooms:
            # TODO: IMPROVEMENT: A user could be part of multiple rooms. There should be a way to execute this iteration as a batch.
            RoomUser.objects.get_or_create(
                room=room,
                user=self.user,
            )
        return rooms

    async def subscribe_to_rooms_activities(self, **kwargs):
        """
        Subscribe to all rooms.
        """
        rooms = await self.get_rooms()
        for room in rooms:
            # subscribe to activities occuring on the RoomUser object
            await self.room_user_activity.subscribe(room_pk=room.pk)
            # subscribe to messages being created/updated in a room.
            await self.message_activity.subscribe(room_pk=room.pk)

    async def unsubscribe_from_all_activities(self, **kwargs):
        """
        Unsubscribe from all rooms
        """
        rooms = await self.get_rooms()
        for room in rooms:
            await self.room_user_activity.unsubscribe(room_pk=room.pk)
            await self.message_activity.unsubscribe(room_pk=room.pk)

    @model_observer(Message, serializer_class=MessageSerializer)
    async def message_activity(self, message: dict, **kwargs):
        self._resolve_is_me(message)
        for reaction in message["reactions"]:
            self._resolve_is_me(reaction)

        # Do not send empty messages and reactions
        if (message["body"] or message["images"]) and not message["is_reaction"]:
            await self.send_json(
                {
                    "messages": [message],
                    "users": [],
                }
            )

    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f"-rooms__{instance.room_user.room.id}"

    @message_activity.groups_for_consumer
    def message_activity(self, consumer, room_pk: str, **kwargs):
        yield f"-rooms__{room_pk}"

    def _resolve_is_me(self, message: dict):
        if not isinstance(message["is_me"], bool):
            message["is_me"] = message["is_me"] == self.user.pk

    @database_sync_to_async
    def user_connect(self):
        user_chat = UserChat.objects.get_user_chat(self.user.pk)
        if not user_chat.is_online:
            user_chat.is_online = True
            user_chat.save()

    @database_sync_to_async
    def user_disconnect(self):
        if self.user.is_authenticated:
            user_chat = UserChat.objects.get_user_chat(self.user.pk)
            if user_chat.is_online:
                user_chat.is_online = False
                user_chat.save()
