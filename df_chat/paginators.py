from rest_framework.pagination import CursorPagination


class RoomCursorPagination(CursorPagination):
    ordering = ('-created_at',)


class ChatMessagePagination(CursorPagination):
    ordering = ('-created_at',)
    page_size = 10
