from django.conf import settings
from rest_framework.settings import APISettings

DEFAULTS = {
    "CHAT_USER_MODEL": settings.AUTH_USER_MODEL,
    # TODO: add default presets
    "REACTION_PRESET": ["👍", "👎"],
}

api_settings = APISettings(getattr(settings, "DF_CHAT", None), DEFAULTS)
