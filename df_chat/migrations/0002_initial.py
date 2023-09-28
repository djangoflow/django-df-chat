# Generated by Django 4.2.5 on 2023-09-27 16:43

from django.db import migrations, models
import django.db.models.deletion

from df_chat.settings import api_settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("df_chat", "0001_initial"),
        migrations.swappable_dependency(api_settings.CHAT_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="roomuser",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=api_settings.CHAT_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="roomuser",
            name="room",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="df_chat.chatroom"
            ),
        ),
        migrations.AddField(
            model_name="roomuser",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=api_settings.CHAT_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="chatroom",
            name="chat_room_avatar",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="df_chat.chatroomavatar",
            ),
        ),
        migrations.AddField(
            model_name="chatmessagereaction",
            name="message",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reactions",
                to="df_chat.chatmessage",
            ),
        ),
        migrations.AddField(
            model_name="chatmessagereaction",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=api_settings.CHAT_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="chatmessagefile",
            name="file",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="df_chat.chatfile",
            ),
        ),
        migrations.AddField(
            model_name="chatmessagefile",
            name="message",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="df_chat.chatmessage",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="in_reply_to",
            field=models.ForeignKey(
                blank=True,
                help_text="Use for replies and sharing messages. Sharing a message is like a reply, but with other room.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="df_chat.chatmessage",
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="room",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="df_chat.chatroom"
            ),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=api_settings.CHAT_USER_MODEL,
            ),
        ),
    ]