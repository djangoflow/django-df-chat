# chat/routing.py
from django.urls import path

from df_chat.asgi.consumers import ChatConsumer

websocket_urlpatterns = [
    path(r"ws/chat/", ChatConsumer.as_asgi()),
]