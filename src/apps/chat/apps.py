from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = "hashid_field.BigHashidAutoField"
    name = "chat"
    api_path = "chat/"
    asgi_prefix = "chat/"

    def ready(self) -> None:
        # Trigger registering signals for model observers
        from chat.asgi.consumers import RoomConsumer  # noqa
