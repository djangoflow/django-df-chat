from df_chat.models import Room
from django.contrib.auth import get_user_model

import factory


User = get_user_model()

TEST_USER_PASSWORD = "secret"


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for django's auth User model
    """

    class Meta:
        model = User

    username = factory.Faker("email")
    password = factory.PostGenerationMethodCall("set_password", TEST_USER_PASSWORD)

    is_active = True


class RoomFactory(factory.django.DjangoModelFactory):
    """
    Factory for chat.models.Room
    """

    class Meta:
        model = Room

    title = factory.Faker("name")
    creator = factory.SubFactory(UserFactory)
