# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0011_auto_20151203_1814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meshterm',
            name='tree_number',
            field=models.CharField(unique=True, max_length=250),
        ),
    ]
