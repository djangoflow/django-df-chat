from django.conf import settings
from django.test import override_settings
from model_bakery import baker
from rest_framework.test import APITestCase

from df_chat import models


class MessageViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.chat_room = baker.make(models.ChatRoom)

        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.user.set_password("test-me")
        self.user.save()

        self.client.login(username=self.user.username, password="test-me")

    def test_creating_a_message_should_add_it_to_db(self) -> None:
        data = {
            "chat_room": self.chat_room.pk,
            "created_by": self.user.pk,
            "message": "Hello World",
            "message_type": models.MessageType.message,
        }
        response = self.client.post(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/", data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            1, models.ChatMessage.objects.filter(message="Hello World").count()
        )

    def test_creating_a_reaction_should_add_it_to_db(self) -> None:
        message = baker.make(models.ChatMessage)

        data = {
            "chat_room": self.chat_room.pk,
            "created_by": self.user.pk,
            "message": "+1",
            "message_type": models.MessageType.reaction,
            "parent": message.pk,
        }
        response = self.client.post(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/", data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            1,
            models.ChatMessage.objects.filter(
                message_type=models.MessageType.reaction
            ).count(),
        )

    def test_message_displays_empty_reactions(self) -> None:
        message = baker.prepare(
            models.ChatMessage,
            chat_room=self.chat_room,
            created_by=self.user,
            message="Hello World",
        )
        message.save()

        response = self.client.get(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/{message.pk}/"
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual([], result["reactions"])

    def test_message_displays_its_reactions(self) -> None:
        message = baker.prepare(
            models.ChatMessage,
            chat_room=self.chat_room,
            created_by=self.user,
            message="Hello World",
        )
        message.save()

        baker.make(
            models.ChatMessage,
            chat_room=self.chat_room,
            message="+1",
            message_type=models.MessageType.reaction,
            parent=message,
        )

        baker.make(
            models.ChatMessage,
            chat_room=self.chat_room,
            message="+1",
            message_type=models.MessageType.reaction,
            parent=message,
        )

        baker.make(
            models.ChatMessage,
            chat_room=self.chat_room,
            message="eyes",
            message_type=models.MessageType.reaction,
            parent=message,
        )

        response = self.client.get(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/{message.pk}/"
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()

        # assert on the correct groupping
        self.assertIn("reactions", result)
        for reaction in result["reactions"]:
            if reaction["content"] == "+1":
                self.assertEqual(2, len(reaction["reactions"]))
            elif reaction["content"] == "eyes":
                self.assertEqual(1, len(reaction["reactions"]))

    def test_disallowed_reactions_are_rejected(self) -> None:
        message = baker.make(models.ChatMessage)

        data = {
            "chat_room": self.chat_room.pk,
            "created_by": self.user.pk,
            # allowed values are defined in tests/settings.py
            "message": "fire",
            "message_type": models.MessageType.reaction,
            "parent": message.pk,
        }
        response = self.client.post(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid reaction", response.json()["errors"][0]["message"])

    def test_unknown_reactions_are_allowed_when_settings_is_empty(self) -> None:
        message = baker.make(models.ChatMessage)

        data = {
            "chat_room": self.chat_room.pk,
            "created_by": self.user.pk,
            "message": "fire",
            "message_type": models.MessageType.reaction,
            "parent": message.pk,
        }

        # allowed values are defined in tests/settings.py
        with override_settings(DF_CHAT_ALLOWED_REACTIONS=()):
            response = self.client.post(
                f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/", data, format="json"
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(
                1,
                models.ChatMessage.objects.filter(
                    message_type=models.MessageType.reaction,
                    message="fire",
                ).count(),
            )

    def test_message_displays_its_replies(self) -> None:
        message = baker.prepare(
            models.ChatMessage,
            chat_room=self.chat_room,
            created_by=self.user,
            message="Hello World",
        )
        message.save()

        baker.make(
            models.ChatMessage,
            chat_room=self.chat_room,
            message="It is a good day today",
            message_type=models.MessageType.response,
            parent=message,
        )

        baker.make(
            models.ChatMessage,
            chat_room=self.chat_room,
            message="Indeed it is",
            message_type=models.MessageType.response,
            parent=message,
        )

        response = self.client.get(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/{message.pk}/"
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()

        # assert on the correct groupping
        self.assertIn("replies", result)
        self.assertEqual(2, len(result["replies"]))
        self.assertEqual("It is a good day today", result["replies"][0]["message"])
        self.assertEqual("Indeed it is", result["replies"][1]["message"])

    def test_message_displays_seen_by_and_received_by(self) -> None:
        message = baker.prepare(
            models.ChatMessage,
            chat_room=self.chat_room,
            created_by=self.user,
            message="Hello World",
        )
        message.save()

        user1 = baker.make(settings.AUTH_USER_MODEL)
        user2 = baker.make(settings.AUTH_USER_MODEL)

        message.received_by.add(user1)
        message.received_by.add(user2)

        message.seen_by.add(user1)

        response = self.client.get(
            f"/api/v1/chat/rooms/{self.chat_room.pk}/messages/{message.pk}/"
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertIn("seen_by", result)
        self.assertEqual(1, len(result["seen_by"]))
        self.assertEqual(user1.pk, result["seen_by"][0]["user_id"])

        self.assertIn("received_by", result)
        self.assertEqual(2, len(result["received_by"]))
        self.assertEqual(user1.pk, result["received_by"][0]["user_id"])
        self.assertEqual(user2.pk, result["received_by"][1]["user_id"])
