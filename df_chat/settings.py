from django.conf import settings
from rest_framework.settings import APISettings

DEFAULTS: dict = {
    "DEFAULT_USER_SERIALIZER_FIELDS": (
        "id",
        "first_name",
        "last_name",
    )
}

api_settings = APISettings(getattr(settings, "DF_CHAT", None), DEFAULTS)
