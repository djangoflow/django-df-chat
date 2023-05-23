from channels.db import database_sync_to_async
from df_chat.models import Room
from df_chat.models import User
from df_chat.tests.utils import RoomFactory
from df_chat.tests.utils import TEST_USER_PASSWORD
from df_chat.tests.utils import UserFactory
from rest_framework.reverse import reverse
from typing import Tuple


class BaseTestUtilsMixin:
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

    def create_room_and_add_users(self, *users) -> Room:
        """
        Creates a Room object and adds the users to it.
        """
        room = RoomFactory()
        room.users.set(users)
        return room

    @database_sync_to_async
    def async_create_user(self) -> Tuple[User, str]:
        """
        Creates a User object and generates an auth token for the user.
        """
        return self.create_user()

    @database_sync_to_async
    def async_create_room_and_add_users(self, *users) -> Room:
        """
        Creates a Room object and adds the users to it.
        """
        return self.create_room_and_add_users(*users)
