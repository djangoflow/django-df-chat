# Generated by Django 4.2.1 on 2023-05-27 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('df_chat', '0002_remove_roomuser_is_online_userchat'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
    ]