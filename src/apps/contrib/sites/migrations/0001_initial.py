# Generated by Django 3.2.9 on 2022-01-24 16:45

import django.contrib.sites.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=100, unique=True, validators=[django.contrib.sites.models._simple_domain_name_validator], verbose_name='domain name')),
                ('name', models.CharField(max_length=50, verbose_name='display name')),
            ],
            options={
                'verbose_name': 'site',
                'verbose_name_plural': 'sites',
                'db_table': 'django_site',
                'ordering': ['domain'],
            },
            managers=[
                ('objects', django.contrib.sites.models.SiteManager()),
            ],
        ),
    ]
