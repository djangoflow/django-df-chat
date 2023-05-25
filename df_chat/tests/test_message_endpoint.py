from datetime import datetime
from datetime import timedelta
from df_chat.models import RoomUser
from df_chat.tests.base import BaseTestUtilsMixin
from django.urls import reverse
from rest_framework.test import APITestCase

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
        body = "Test message 1234."
        response = self.client.post(message_endpoint, {"body": body})
        message = response.json()

        room_user = user.roomuser_set.get()
        self.assertEqual(message["body"], body)
        self.assertTrue(message["is_me"])
        self.assertEqual(message["room_user_id"], room_user.pk)
        self.assertIsNone(message["parent_id"])
        self.assertFalse(message["is_reaction"])
        self.assertEqual(response.status_code, http.HTTPStatus.CREATED)

        return user, room

    def test_filter_message_by_keyword(self):
        """
        Test-case for filtering messages by the `Message` model's `body` field.
        """
        _, room = self.test_message_creation_success()
        messages_list_endpoint = reverse(
            "rooms-messages-list", kwargs={"room_pk": room.pk}
        )

        for body in [
            "Test message 1234.",
            "Test message 1234",
            "Test",
            "test",
            "Message",
            "message",
            "1234",
        ]:
            messages_list_response = self.client.get(
                messages_list_endpoint,
                {"body": body},
            )
            # Assert the correct HTTP status code for response.
            self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
            # Assert the response body contains the keyword.
            self.assertIn(
                body.lower(), messages_list_response.json()[0]["body"].lower()
            )

        for body in [
            "somethingrandom",
            "messages",
            "124",
        ]:
            messages_list_response = self.client.get(
                messages_list_endpoint,
                {"body": body},
            )
            # Assert the correct HTTP status code for response.
            self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)

    def test_filter_message_by_username(self):
        """
        Test-case for filtering messages by the `Message` model's related `User`'s `username` field.
        """
        user, room = self.test_message_creation_success()
        messages_list_endpoint = reverse(
            "rooms-messages-list", kwargs={"room_pk": room.pk}
        )

        messages_list_response = self.client.get(
            messages_list_endpoint,
            {"username": user.username},
        )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert the message `room_user_id` matches the `id` field of the `RoomUser` object
        #   corresponding to the user.
        room_user_obj = RoomUser.objects.get(user__id=user.id)
        self.assertEqual(
            messages_list_response.json()[0]["room_user_id"], room_user_obj.id
        )

        messages_list_response = self.client.get(
            messages_list_endpoint,
            {"username": "invalid_username"},
        )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)

    def test_filter_message_by_date_range(self):
        """
        Test-case for filtering messages by the `Message` model's `created` field.
        """
        user, room = self.test_message_creation_success()
        messages_list_endpoint = reverse(
            "rooms-messages-list", kwargs={"room_pk": room.pk}
        )

        now = datetime.now()
        before = now - timedelta(hours=1)
        datetime_format = "%Y-%m-%dT%H:%M:%S.%f"

        messages_list_response = self.client.get(
            messages_list_endpoint,
            {"created_gte": str(before)},
        )
        message_created = datetime.strptime(
            messages_list_response.json()[0]["created"], datetime_format
        )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert message `created` datetime is larger than `before` datetime.
        self.assertTrue(message_created >= before)

        # * datetime range search - range end
        messages_list_response = self.client.get(
            messages_list_endpoint,
            {"created_lte": str(now)},
        )
        message_created = datetime.strptime(
            messages_list_response.json()[0]["created"], datetime_format
        )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert message `created` datetime is smaller than `now` datetime.
        self.assertTrue(message_created <= now)

        # * datetime range search - now results
        messages_list_response = self.client.get(
            messages_list_endpoint,
            {"created_lte": str(before)},
        )
        # Assert the correct HTTP status code for response.
        self.assertEqual(messages_list_response.status_code, http.HTTPStatus.OK)
        # Assert no  messages are created after `before` time.
        self.assertEqual(messages_list_response.json(), [])

    # TODOS: We should also implement the following tests:
    # - Fail to create a message when the user is not authenticated.
    # - Ensure that the endpoint returns a 404 error
    #   - if the user is not part of a Room
    #   - if a room doesn't exist at all.
