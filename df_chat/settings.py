from django.conf import settings
from rest_framework.settings import APISettings

DEFAULTS: dict = {}

api_settings = APISettings(getattr(settings, "DF_CHAT", None), DEFAULTS)
