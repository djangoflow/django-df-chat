from rest_framework.pagination import CursorPagination


class ChatRoomPagination(CursorPagination):
    ordering = ("-last_message_id",)
    page_size = 10


class ChatMessagePagination(CursorPagination):
    ordering = ("-created",)
    page_size = 10
