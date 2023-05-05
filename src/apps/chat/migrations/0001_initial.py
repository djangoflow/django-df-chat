# Generated by Django 4.0.8 on 2023-05-05 11:05

import chat.models
import core.imagekit.fields
import df_notifications.fields
import df_notifications.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import hashid_field.field
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('df_notifications', '0006_alter_userdevice_registration_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', hashid_field.field.BigHashidAutoField(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', auto_created=True, min_length=13, prefix='', primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('is_reaction', models.BooleanField(default=False)),
                ('body', models.TextField(default='')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='chat.message')),
                ('received_by', models.ManyToManyField(blank=True, related_name='message_received_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', hashid_field.field.BigHashidAutoField(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', auto_created=True, min_length=13, prefix='', primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=512)),
                ('description', models.TextField(blank=True, default='')),
                ('image', core.imagekit.fields.FullImageField(blank=True, null=True, upload_to=chat.models.Room.get_upload_to)),
                ('is_public', models.BooleanField(default=True)),
                ('admins', models.ManyToManyField(blank=True, related_name='rooms_admin_set', to=settings.AUTH_USER_MODEL)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms_creator_set', to=settings.AUTH_USER_MODEL)),
                ('muted_by', models.ManyToManyField(blank=True, related_name='room_muted_set', to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-modified', 'title'),
            },
        ),
        migrations.CreateModel(
            name='RoomUser',
            fields=[
                ('id', hashid_field.field.BigHashidAutoField(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', auto_created=True, min_length=13, prefix='', primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('is_online', models.BooleanField(default=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.room')),
                ('user', models.ForeignKey(blank=True, help_text='Leave empty for a system message', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MessageNotificationRule',
            fields=[
                ('id', hashid_field.field.BigHashidAutoField(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', auto_created=True, min_length=13, prefix='', primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', df_notifications.fields.NoMigrationsChoicesField(max_length=255)),
                ('template_prefix', models.CharField(max_length=255)),
                ('context', models.JSONField(blank=True, default=dict)),
                ('history', models.ManyToManyField(blank=True, editable=False, to='df_notifications.notificationhistory')),
            ],
            options={
                'abstract': False,
            },
            bases=(df_notifications.models.GenericBase, models.Model),
        ),
        migrations.CreateModel(
            name='MessageImage',
            fields=[
                ('id', hashid_field.field.BigHashidAutoField(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', auto_created=True, min_length=13, prefix='', primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('image', core.imagekit.fields.FullImageField(blank=True, null=True, upload_to=chat.models.MessageImage.get_upload_to)),
                ('width', models.IntegerField(default=500)),
                ('height', models.IntegerField(default=300)),
                ('size', models.IntegerField(default=0)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='chat.message')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='message',
            name='room_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.roomuser'),
        ),
        migrations.AddField(
            model_name='message',
            name='seen_by',
            field=models.ManyToManyField(blank=True, related_name='message_seen_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
