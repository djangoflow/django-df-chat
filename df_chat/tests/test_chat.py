from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from df_chat.models import Message
from df_chat.models import RoomUser
from df_chat.models import User
from df_chat.tests.utils import RoomFactory
from df_chat.tests.utils import TEST_USER_PASSWORD
from df_chat.tests.utils import UserFactory
from django.test import TransactionTestCase, AsyncClient
from rest_framework.reverse import reverse
from tests.asgi import application
from datetime import datetime, timedelta
import http
from typing import Tuple
import os


class TestChat(TransactionTestCase):
    """
    Test for chat application
    """

    def setUp(self) -> None:
        """
        Set-up tasks for this test-case.
        """
        super().setUp()
        # * Creates an asynchronous client.
        self.async_client = AsyncClient()

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

    async def test_create_message(self):
        """
        Happy test-case for creating a message.
        The purpose of this is test is to make sure we can successfully create a user,
            create a room with that user, and create a message corresponding to the created room.
        In-order to do so, the following steps must be taken:
            1. Create a `user` (superuser) object.
            2. Create a `room` object and add the `user` created in step 1 to its users.
            3. Create a `message` object corresponding to the `room` created in step 2.
        """
        # ! Temp hacky fix for the `self.async_client` usages within this method.
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        # * Step 1
        # We utilize the existing method to create a random user.
        user, _ = await self.create_user()
        
        # * Step 2
        # We also utilize the existing method to create a room and add the
        #   previously created user to it.
        room = await self.create_room_and_add_users(user)

        # Login for session authentication for the message create API.
        self.async_client.login(username=user.username, password=TEST_USER_PASSWORD)

        # * Step 3
        body = "Test message 1234."
        message_create_response = await self.async_client.post(
            f"/api/v1/chat/rooms/{room.id}/messages/",
            data={"body": body},
        )
        # Assert the correct HTTP status code for response.
        self.assertEqual(message_create_response.status_code, http.HTTPStatus.CREATED)
        # Assert the message data is correct.
        self.assertEqual(message_create_response.json()["room_id"], room.id)
        self.assertEqual(message_create_response.json()["body"], body)
    
        return user, room

    async def test_filter_message(self):
        """
        Test-case for filtering messages.
        The purpose of this is test is to perform multiple filters on the
            message list API. These filters include:
        1. Filter by `body` field (keyword sear ch).
        2. Filter by `User`'s `username` field.   
        3. Filter by `created` field (datetime range).
        In-order to do so, we test multiple cases against the message created
            in the `test_create_message` test.
        """
        # We need the user and the room from the `test_create_message` test in-order to filter on its messages.
        user, room = await self.test_create_message()
        
        messages_list_api_url = f"/api/v1/chat/rooms/{room.id}/messages/"
        
        # * 1. Keyword search - ok cases
        for body in [
            "Test message 1234.",
            "Test message 1234",
            "Test",
            "test",
            "Message",
            "message",
            "1234",
        ]:
            messages_list_response = await self.async_client.get(
                messages_list_api_url,
                {"body": body},
            )
            # Assert the correct HTTP status code for response.
            self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
            # Assert the response body contains the keyword.
            self.assertIn(body.lower(), messages_list_response.json()[0]["body"].lower())
        
        # * 1. Keyword search - not ok cases
        for body in [
            "somethingrandom",
            "messages",
            "124",
        ]:
            messages_list_response = await self.async_client.get(
                messages_list_api_url,
                {"body": body},
            )
            # Assert the correct HTTP status code for response.
            self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)

        # * 2. username search - ok case
        messages_list_response = await self.async_client.get(
                messages_list_api_url,
                {"username": user.username},
            )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert the message `room_user_id` matches the `id` field of the `RoomUser` object
        #   corresponding to the user.
        room_user_obj = RoomUser.objects.get(user__id=user.id)
        self.assertEqual(messages_list_response.json()[0]['room_user_id'], room_user_obj.id)

        # * 2. username search - not ok case
        messages_list_response = await self.async_client.get(
                messages_list_api_url,
                {"username": "invalid_username"},
            )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)

        now = datetime.now()
        before = now - timedelta(hours=1)
        datetime_format = "%Y-%m-%dT%H:%M:%S.%f"

        # * datetime range search - range start
        messages_list_response = await self.async_client.get(
                messages_list_api_url,
                {"created_gte": str(before)},
            )
        message_created = datetime.strptime(messages_list_response.json()[0]["created"], datetime_format)
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert message `created` datetime is larger than `before` datetime.
        self.assertTrue(message_created >= before)

        # * datetime range search - range end
        messages_list_response = await self.async_client.get(
                messages_list_api_url,
                {"created_lte": str(now)},
            )
        message_created = datetime.strptime(messages_list_response.json()[0]["created"], datetime_format)
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert message `created` datetime is smaller than `now` datetime.
        self.assertTrue(message_created <= now)


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
