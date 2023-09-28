from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from df_chat.models import ChatRoom


class ChatRoomViewSetTestCase(APITestCase):
    def setUp(self):
        self.chat_room_url = reverse("chat_room-list")

    def test_list_chat_rooms(self):
        ChatRoom.objects.create(name="Room 1", description="Description 1")
        ChatRoom.objects.create(name="Room 2", description="Description 2")

        response = self.client.get(self.chat_room_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 2)
