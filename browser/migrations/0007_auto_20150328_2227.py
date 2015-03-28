# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0006_auto_20150328_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchresult',
            name='ended_processing',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='searchresult',
            name='started_processing',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
