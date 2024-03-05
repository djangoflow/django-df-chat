from django.conf import settings
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
