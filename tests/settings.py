from datetime import timedelta
from pathlib import Path


DEBUG = True

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent

ROOT_URLCONF = "tests.urls"
SECRET_KEY = "111111"
HASHID_FIELD_SALT = "111111"
HASHID_FIELD_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "fcm_django",
    "df_notifications",
    "django_slack",
    "import_export",
    "tests.test_app.apps.TestAppConfig",
    "django_celery_beat",
    "otp_twilio",
    "df_chat",
    "django_extensions",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "debug_toolbar",
    "django_filters",
]

GRAPH_MODELS = {
    "group_models": True,
}

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]


INTERNAL_IPS = [
    "127.0.0.1",
]

SITE_ID = 1

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

STATIC_URL = "/static/"
STATIC_ROOT = str(ROOT_DIR / "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = str(ROOT_DIR / "mediafiles")

ALLOWED_HOSTS = ["*"]

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
ASGI_APPLICATION = "tests.asgi.application"


DF_NOTIFICATIONS = {
    "CHANNELS": {
        "email": "df_notifications.channels.EmailChannel",
        "console": "df_notifications.channels.ConsoleChannel",
        "push": "df_notifications.channels.FirebasePushChannel",
        "webhook": "df_notifications.channels.JSONPostWebhookChannel",
        "slack": "df_notifications.channels.SlackChannel",
        "test": "tests.channels.TestChannel",
    },
    "SAVE_HISTORY_CONTENT": True,
    "REMINDERS_CHECK_PERIOD": 5,
}


DF_AUTH = {
    "USER_IDENTITY_FIELDS": ("username",),
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "tests.schema.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=2),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "DF Chat API",
    "DESCRIPTION": "DF Chat API (Django)",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    # "ENUM_NAME_OVERRIDES": {"GenderEnum": "accounts.models.Gender"},
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
}
