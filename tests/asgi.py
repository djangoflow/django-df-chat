from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from django.core.asgi import get_asgi_application

import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django_asgi_app = get_asgi_application()

from .async_router import urlpatterns  # noqa
from df_chat.middleware import JWTAuthMiddlewareStack  # noqa


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(urlpatterns)),
    }
)
