DF_CHAT_INSTALLED_APPS = [
    "df_chat",
]


def get_redis_channel_layer(REDIS_URLS: str = "redis://localhost:6379/0") -> dict:
    return {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": REDIS_URLS.split(","),
            },
        },
    }


# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [os.getenv("REDIS_URL", "localhost:6379"),],
#         },
#     },
# }
