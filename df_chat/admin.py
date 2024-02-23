from django.contrib import admin

from df_chat.models import ChatMember, ChatMessage, ChatRoom, MemberChannel


@admin.register(MemberChannel)
class MemberChannelAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "user")


class ChatUserInline(admin.TabularInline):
    model = ChatMember


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "title")
    inlines = (ChatUserInline,)


@admin.register(ChatMember)
class ChatMembersAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "chat_room",
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_by",
        "message",
    )
