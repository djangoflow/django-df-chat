from rest_framework.pagination import CursorPagination


class ChatMessagePagination(CursorPagination):
    ordering = ('-created_at',)
    page_size = 10
