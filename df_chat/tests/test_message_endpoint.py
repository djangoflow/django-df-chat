from df_chat.models import RoomUser
from df_chat.tests.base import BaseTestUtilsMixin
from django.urls import reverse
from rest_framework.test import APITestCase
from datetime import datetime, timedelta
import http


class TestMessageEndpoint(APITestCase, BaseTestUtilsMixin):
    """
    Testing the RESTful API messages endpoint
    """

    def test_message_creation_success(self):
        """
        Testing creation of a message using the messages endpoint.
        """
        user, token = self.create_user()
        room = self.create_room_and_add_users(user)

        message_endpoint = reverse("rooms-messages-list", kwargs={"room_pk": room.pk})
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        response = self.client.post(message_endpoint, {"body": "Hi"})
        message = response.json()

        room_user = user.roomuser_set.get()
        self.assertEqual(message["body"], "Hi")
        self.assertTrue(message["is_me"])
        self.assertEqual(message["room_user_id"], room_user.pk)
        self.assertIsNone(message["parent_id"])
        self.assertFalse(message["is_reaction"])
        self.assertEqual(response.status_code, http.HTTPStatus.CREATED)

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
        user, room = await self.test_message_creation_success()
        
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


    # TODOS: We should also implement the following tests:
    # - Fail to create a message when the user is not authenticated.
    # - Ensure that the endpoint returns a 404 error
    #   - if the user is not part of a Room
    #   - if a room doesn't exist at all.
