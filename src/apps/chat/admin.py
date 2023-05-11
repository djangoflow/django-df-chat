from django.contrib import admin
from .models import Message, MessageImage, Room, RoomUser,\
    Category


class RoomUserInline(admin.TabularInline):
    model = RoomUser


@admin.register(RoomUser)
class RoomUserAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "is_active", "is_online")
    list_filter = ("is_active", "is_online", "room__title")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "modified",
        'id',
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        'id',
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
