from .models import Message
from .models import MessageImage
from .models import Room
from .models import RoomUser
from .models import Category
from .models import UserChat
from django.contrib import admin


@admin.register(UserChat)
class UserChatAdmin(admin.ModelAdmin):
    list_display = ("user", "is_online")
    list_filter = ("is_online",)


class RoomUserInline(admin.TabularInline):
    model = RoomUser


@admin.register(RoomUser)
class RoomUserAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "is_active")
    list_filter = ("is_active", "room__title")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "title",
        "modified",
        'id',
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "creator",
        "created",
    )


class MessageImageInline(admin.TabularInline):
    model = MessageImage


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    def room(self, obj):
        return obj.room_user.room

    list_display = ("room", "body", "room_user", "parent", "created", "modified")
