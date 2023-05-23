from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from df_chat.models import Message
from df_chat.models import RoomUser
from df_chat.models import User
from df_chat.tests.utils import RoomFactory
from df_chat.tests.utils import TEST_USER_PASSWORD
from df_chat.tests.utils import UserFactory
from django.test import TransactionTestCase
from rest_framework.reverse import reverse
from tests.asgi import application
from typing import Tuple


class TestChat(TransactionTestCase):
    """
    Test for chat appplication
    """

    @database_sync_to_async
    def create_user(self) -> Tuple[User, str]:
        """
        Creates a User object and generates an auth token for the user.
        """
        user = UserFactory()
        # User has to use an authentication token in order to connect with the websocket endpoint.
        auth_token_url = reverse("token-list")
        response = self.client.post(
            auth_token_url,
            data={"username": user.username, "password": TEST_USER_PASSWORD},
        )
        token = response.json()["token"]
        return user, token

    @database_sync_to_async
    def create_room_and_add_users(self, *users):
        """
        Creates a Room object and adds the users to it.
        """
        room = RoomFactory()
        room.users.set(users)
        return room

    async def test_invalid_websocket_path(self):
        """
        We should reject the connection, if an invalid route is provided.
        """
        communicator = WebsocketCommunicator(application, "ws/dummy")
        with self.assertRaisesMessage(ValueError, "No route found for path 'ws/dummy'"):
            await communicator.connect()

    async def test_auth(self):
        """
        Ensures that the authenticated user is added to the scope of the websocket consumer.
        """
        user, token = await self.create_user()
        communicator = WebsocketCommunicator(application, f"ws/chat/?token={token}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        # Checking that our user was added to the scope.
        self.assertEqual(communicator.scope["user"], user)
        await communicator.disconnect()

    async def test_chat_single_room(self):
        """
        An end-to-end test case to test the happy-path-flow of a chat between two users in a single room.
        """
        # creating a room with two users
        user1, token1 = await self.create_user()
        user2, token2 = await self.create_user()
        room = await self.create_room_and_add_users(user2, user1)

        # connecting our first user to the chat websocket endpoint
        communicator1 = WebsocketCommunicator(application, f"ws/chat/?token={token1}")
        await communicator1.connect()

        # As of now, there are no messages in the room
        # The WebsocketCommunicator.receive_nothing returns a True, if there is no message to receive.
        self.assertTrue(await communicator1.receive_nothing())

        # connecting our second user to the chat websocket endpoint
        communicator2 = WebsocketCommunicator(application, f"ws/chat/?token={token2}")
        await communicator2.connect()

        # When another user connects to our app and is part of the room of the first user,
        # the first user will receive a json dict stating that a user
        # has been connected.
        event = await communicator1.receive_json_from()
        room_user2 = await database_sync_to_async(RoomUser.objects.get)(
            room=room, user=user2
        )
        self.assertEqual(
            event["users"][0],
            {
                "id": room_user2.id,
                "is_me": False,
                "is_online": True,
                "is_active": True,
                "room_id": room.id,
            },
        )
        # But, no messages are sent by the second user.
        self.assertEqual(len(event["messages"]), 0)

        room_user1 = await database_sync_to_async(RoomUser.objects.get)(
            room=room, user=user1
        )

        # If a Message object is created, it should be received by both users
        await database_sync_to_async(Message.objects.create)(
            room_user=room_user1, body="Hi"
        )
        event1 = await communicator1.receive_json_from()
        event2 = await communicator2.receive_json_from()
        # Only one message will be received by each user
        self.assertEqual(len(event1["messages"]), 1)
        self.assertEqual(len(event2["messages"]), 1)
        message_received_by_user1 = event1["messages"][0]
        message_received_by_user2 = event2["messages"][0]
        self.assertEqual(message_received_by_user1["body"], "Hi")
        self.assertEqual(message_received_by_user1["room_id"], room.id)
        self.assertEqual(message_received_by_user1["room_user_id"], room_user1.id)
        self.assertEqual(message_received_by_user1["is_me"], True)
        self.assertEqual(message_received_by_user2["is_me"], False)
        # Except for "is_me", everything else in the message is same for both the users
        del message_received_by_user1["is_me"]
        del message_received_by_user2["is_me"]
        self.assertDictEqual(message_received_by_user1, message_received_by_user2)

        # Finally, disconnecting all the users
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_chat_multiple_rooms(self):
        """
        An end-to-end test case to test the happy-path-flow of a chat for a user connected to multiple rooms.
        """
        # creating three users
        user1, token1 = await self.create_user()
        user2, token2 = await self.create_user()
        user3, token3 = await self.create_user()
        # creating two rooms, where user1 is present in both.
        room_of_user1_and_user2 = await self.create_room_and_add_users(user1, user2)
        room_of_user1_and_user3 = await self.create_room_and_add_users(user1, user3)

        # connecting the first, second and third users to the chat websocket endpoint, simultaneously
        communicator1 = WebsocketCommunicator(application, f"ws/chat/?token={token1}")
        await communicator1.connect()
        communicator2 = WebsocketCommunicator(application, f"ws/chat/?token={token2}")
        await communicator2.connect()
        communicator3 = WebsocketCommunicator(application, f"ws/chat/?token={token3}")
        await communicator3.connect()

        # When another user connects to a room, the first user will receive a json dict stating that a user
        # has connected to the room.
        # Here user2 has connected to our app. So the common room of user1 and user2 should be notified.
        event_when_user2_connected_to_room_of_user1_and_user2 = (
            await communicator1.receive_json_from()
        )
        room_user_of_room_of_user1_and_user2_for_user2 = await database_sync_to_async(
            RoomUser.objects.get
        )(room=room_of_user1_and_user2, user=user2)
        self.assertEqual(
            event_when_user2_connected_to_room_of_user1_and_user2["users"][0]["id"],
            room_user_of_room_of_user1_and_user2_for_user2.pk,
        )
        self.assertEqual(
            event_when_user2_connected_to_room_of_user1_and_user2["users"][0][
                "room_id"
            ],
            room_of_user1_and_user2.pk,
        )

        # Also, as user3 connected to the app, the common room of user1 and user3 should be notified.
        event_when_user3_connected_to_room_of_user1_and_user3 = (
            await communicator1.receive_json_from()
        )
        room_user_of_room_of_user1_and_user3_for_user3 = await database_sync_to_async(
            RoomUser.objects.get
        )(room=room_of_user1_and_user3, user=user3)
        self.assertEqual(
            event_when_user3_connected_to_room_of_user1_and_user3["users"][0]["id"],
            room_user_of_room_of_user1_and_user3_for_user3.pk,
        )
        self.assertEqual(
            event_when_user3_connected_to_room_of_user1_and_user3["users"][0][
                "room_id"
            ],
            room_of_user1_and_user3.pk,
        )

        # ### Testing Messages
        # If user3 creates a message in room_of_user1_and_user2,
        # user1 and user2 should be notified, but user3 should not be notified.
        await database_sync_to_async(Message.objects.create)(
            room_user=room_user_of_room_of_user1_and_user2_for_user2, body="Hi"
        )
        event_for_user1_when_user2_created_a_messsage_in_room_of_user1_and_user2 = (
            await communicator1.receive_json_from()
        )
        self.assertEqual(
            event_for_user1_when_user2_created_a_messsage_in_room_of_user1_and_user2[
                "messages"
            ][0]["room_user_id"],
            room_user_of_room_of_user1_and_user2_for_user2.pk,
        )
        self.assertEqual(
            event_for_user1_when_user2_created_a_messsage_in_room_of_user1_and_user2[
                "messages"
            ][0]["is_me"],
            False,
        )
        self.assertEqual(
            event_for_user1_when_user2_created_a_messsage_in_room_of_user1_and_user2[
                "messages"
            ][0]["room_id"],
            room_of_user1_and_user2.pk,
        )

        event_for_user2_when_user2_created_a_messsage_in_room_of_user1_and_user2 = (
            await communicator2.receive_json_from()
        )
        self.assertEqual(
            event_for_user2_when_user2_created_a_messsage_in_room_of_user1_and_user2[
                "messages"
            ][0]["room_user_id"],
            room_user_of_room_of_user1_and_user2_for_user2.pk,
        )
        self.assertEqual(
            event_for_user2_when_user2_created_a_messsage_in_room_of_user1_and_user2[
                "messages"
            ][0]["is_me"],
            True,
        )
        self.assertEqual(
            event_for_user2_when_user2_created_a_messsage_in_room_of_user1_and_user2[
                "messages"
            ][0]["room_id"],
            room_of_user1_and_user2.pk,
        )

        # Ensuring that user3 is not notified about the message in room_of_user1_and_user2
        self.assertTrue(await communicator3.receive_nothing())

        # Finally, disconnecting all the users
        await communicator1.disconnect()
        await communicator2.disconnect()
        await communicator3.disconnect()


# TODO: Trying to connect without providing a token results in an error
#  "ValueError: 'AnonymousUser' value must be a positive integer or a valid Hashids string."
# We should return a permission denied message via the websocket and gracefully disconnect the user.
# TODO: In the current approach, in order to create a message in a room, a user should make a HTTP POST request.
# And then the message is propagated to all the listeners in that room.
# But, chatting is done in real-time. Users expect to send and receive messages real quick.
# An HTTP connection not stateful. It takes time to connect. And disconnects immediately once the request is fulfiled.
# On the other hand, a websocket connection is stateful - the connection is live until either party terminates it.
# So, using websockets we could communicate in real time.
# - we should allow users to create messages via websocket instead of HTTP.
