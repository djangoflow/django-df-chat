from datetime import datetime
from df_chat.models import Message
from df_chat.models import RoomUser
from df_chat.tests.base import BaseTestUtilsMixin
from django.urls import reverse
from rest_framework.test import APITestCase

import http


class TestMessageEndpoint(APITestCase, BaseTestUtilsMixin):
    """
    Testing the RESTful API messages endpoint
    """

    def __message_endpoint(self, room_pk):
        return reverse("rooms-messages-list", kwargs={"room_pk": room_pk})

    def test_message_creation_success(self, body="hi"):
        """
        Testing creation of a message using the messages endpoint.
        """
        user, token = self.create_user()
        room = self.create_room_and_add_users(user)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        response = self.client.post(self.__message_endpoint(room.pk), {"body": body})
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
        _, room = self.test_message_creation_success(body="Test message 1234.")

        for body in [
            "Test message 1234.",
            "Test message 1234",
            "Test",
            "test",
            "Message",
            "message",
            "1234",
        ]:
            response = self.client.get(
                self.__message_endpoint(room.pk),
                {"body": body},
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertIn(body.lower(), response.json()[0]["body"].lower())

        for body in [
            "somethingrandom",
            "messages",
            "124",
        ]:
            response = self.client.get(
                self.__message_endpoint(room.pk),
                {"body": body},
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(response.json(), [])

    def test_filter_message_by_username(self):
        """
        Test-case for filtering messages by the `Message` model's related `User`'s `username` field.
        """
        user, room = self.test_message_creation_success()

        response = self.client.get(
            self.__message_endpoint(room.pk),
            {"username": user.username},
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        room_user_obj = RoomUser.objects.get(user__id=user.id)
        self.assertEqual(response.json()[0]["room_user_id"], room_user_obj.id)

        response = self.client.get(
            self.__message_endpoint(room.pk),
            {"username": "invalid_username"},
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.json(), [])

    def test_filter_message_by_date_range(self):
        """
        Test-case for filtering messages by the `Message` model's `created` field.
        What we should see in these cases:
            1. Before `timestamp_0` ~> count = 0
            2. After `timestamp_0` ~> count = 3
            3. Between each timestamp ~> count = 1
            4. Before `timestamp_3` ~> count = 3
            5. After `timestamp_3` ~> count = 0
        """
        datetime_format = "%Y-%m-%dT%H:%M:%S.%f"

        timestamp_0 = datetime.now()
        user, room = self.test_message_creation_success()
        timestamp_1 = datetime.now()
        Message.objects.create(
            room_user=RoomUser.objects.get(user=user, room=room),
            body="hi",
        )
        timestamp_2 = datetime.now()
        Message.objects.create(
            room_user=RoomUser.objects.get(user=user, room=room),
            body="hi",
        )
        timestamp_3 = datetime.now()

        # * 1
        response = self.client.get(
            self.__message_endpoint(room.pk),
            {"created_lte": str(timestamp_0)},
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(len(response.json()), 0)

        # * 2
        response = self.client.get(
            self.__message_endpoint(room.pk),
            {"created_gte": str(timestamp_0)},
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(len(response.json()), 3)
        # To assert the `created` of all messages are indeed larger than `timestamp_0`.
        self.assertTrue(
            all(
                created >= timestamp_0
                for created in [
                    datetime.strptime(message["created"], datetime_format)
                    for message in response.json()
                ]
            )
        )

        # * 3
        for datetime_range in [
            (timestamp_0, timestamp_1),
            (timestamp_1, timestamp_2),
            (timestamp_2, timestamp_3),
        ]:
            response = self.client.get(
                self.__message_endpoint(room.pk),
                {
                    "created_gte": str(datetime_range[0]),
                    "created_lte": str(datetime_range[1]),
                },
            )
            message_created = datetime.strptime(
                response.json()[0]["created"], datetime_format
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(len(response.json()), 1)
            self.assertTrue(datetime_range[0] <= message_created <= datetime_range[1])

        # * 4
        response = self.client.get(
            self.__message_endpoint(room.pk),
            {"created_lte": str(timestamp_3)},
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(len(response.json()), 3)
        # To assert the `created` of all messages are indeed smaller than `timestamp_3`.
        self.assertTrue(
            all(
                created <= timestamp_3
                for created in [
                    datetime.strptime(message["created"], datetime_format)
                    for message in response.json()
                ]
            )
        )

        # * 5
        response = self.client.get(
            self.__message_endpoint(room.pk),
            {"created_gte": str(timestamp_3)},
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(len(response.json()), 0)

    # TODOS: We should also implement the following tests:
    # - Fail to create a message when the user is not authenticated.
    # - Ensure that the endpoint returns a 404 error
    #   - if the user is not part of a Room
    #   - if a room doesn't exist at all.
