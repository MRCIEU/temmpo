# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-06-10 18:19
from __future__ import unicode_literals

from datetime import timedelta

from django.db import migrations
from django.utils import timezone

def create_reprocessing_message(apps, schema_editor):
    msg = "Due to improvements in the matching algorithm, all results are being reprocessed. Any changes will be highlighted in the Results area. NB: This may take up to 48 hours and new search results will be delayed."
    Message = apps.get_model("browser", "Message")
    User = apps.get_model("auth", "User")
    initial_user = User.objects.get(id=1)
    # Add a message set to clear in a week.
    # With expectation that after manual check the message will be disabled upon completion of the migration.
    new_msg = Message.objects.create(body=msg, user=initial_user, end=timezone.now() + timedelta(days=7))
    new_msg.save()


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0022_message'),
    ]

    operations = [
    ]