import os

DF_CHAT_INSTALLED_APPS = [
    "df_chat",
]


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://redis:6379"),],
        },
    },
}
