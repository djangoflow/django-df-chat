from channels.db import database_sync_to_async
from df_chat.drf.serializers import MessageSerializer
from df_chat.drf.serializers import RoomSerializer
from df_chat.drf.serializers import RoomUserSerializer
from df_chat.models import Message
from df_chat.models import Room
from df_chat.models import RoomUser
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer import ModelObserver


def post_init_receiver(self, instance, **kwargs):
    self.get_observer_state(instance).current_groups = set()


ModelObserver.post_init_receiver = post_init_receiver


class RoomConsumer(GenericAsyncAPIConsumer):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    user = None

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.check_room()
        await self.user_connect()
        # TODO(eugapx) subscribe to group for this room only instead of one global group
        # so that when you broadcast messages you broarcast them only to the consumers in one room
        # instead of broadcasting all messages to all consumers
        # so that peeople in private group can't hack messages in private group that they receive

        await self.room_user_activity.subscribe()
        await self.message_activity.subscribe()
        await self.accept()

    async def disconnect(self, close_code):
        await self.message_activity.unsubscribe()
        await self.room_user_activity.unsubscribe()
        await self.user_disconnect()

    @model_observer(RoomUser)
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
    def room_user_activity(self, consumer, **kwargs):
        yield f"-room__{consumer.room_id}"

    @room_user_activity.serializer
    def room_user_activity(self, instance: RoomUser, action, **kwargs) -> dict:
        """This will return the room_user serializer"""
        return RoomUserSerializer(instance).data

    @model_observer(Message)
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
        yield f"-room__{instance.room_user.room_id}"

    @message_activity.groups_for_consumer
    def message_activity(self, consumer, **kwargs):
        yield f"-room__{consumer.room_id}"

    @message_activity.serializer
    def message_activity(self, instance: Message, action, **kwargs) -> dict:
        """This will return the message serializer"""
        return MessageSerializer(instance).data

    def _resolve_is_me(self, message: dict):
        if not isinstance(message["is_me"], bool):
            message["is_me"] = message["is_me"] == str(self.room_user.id)

    @database_sync_to_async
    def check_room(self):
        self.room = Room.objects.filter_for_user(self.scope["user"]).get(
            pk=self.room_id
        )

    @database_sync_to_async
    def user_connect(self):
        user = RoomUser.objects.get_room_user(
            room_pk=self.room_id,
            user_pk=self.user.pk,
        )
        if not user.is_online:
            user.is_online = True
            user.save()
        self.room_user = user

    @database_sync_to_async
    def user_disconnect(self):
        if self.user.is_authenticated:
            user = RoomUser.objects.filter(
                user=self.scope["user"], room_id=self.room_id, is_active=True
            ).first()
            if user:
                user.is_online = False
                user.save()
