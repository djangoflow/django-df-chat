from channels.routing import URLRouter
from df_chat.asgi.urls import urlpatterns
from django.urls import path


urlpatterns = [path("ws/chat", URLRouter(urlpatterns))]
