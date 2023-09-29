from django.contrib import admin

from tests.test_app.models import ChatUser, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(ChatUser)
class ChatUserAdmin(admin.ModelAdmin):
    pass
