from df_chat.constants import ROOM_CHAT_ALIAS
from df_chat.models import MemberChannel
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class DynamicUserGroupSubscriptionHandler(object):
    def __init__(self):
        self.channel_layer = get_channel_layer()

    def unsubscribe(self, user_id, room_id):
        channels = MemberChannel.objects.subscribed_channels(user_id).values_list("channel_name", flat=True)
        for channel in channels:
            async_to_sync(self.channel_layer.group_discard)(
                ROOM_CHAT_ALIAS.format(room_id=room_id), channel
            )

    def subscribe(self, user_id, room_id):
        channels = MemberChannel.objects.subscribed_channels(user_id).values_list("channel_name", flat=True)
        for channel in channels:
            async_to_sync(self.channel_layer.group_add)(
                ROOM_CHAT_ALIAS.format(room_id=room_id), channel
            )
