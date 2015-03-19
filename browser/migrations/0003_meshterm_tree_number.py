# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0002_auto_20150318_1525'),
    ]

    operations = [
        migrations.AddField(
            model_name='meshterm',
            name='tree_number',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]
