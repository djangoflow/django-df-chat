from rest_framework.pagination import LimitOffsetPagination


class ChatRoomPagination(LimitOffsetPagination):
    ordering = ("-last_message_id",)
    page_size = 10


class ChatMessagePagination(LimitOffsetPagination):
    ordering = ("-created",)
    page_size = 10
