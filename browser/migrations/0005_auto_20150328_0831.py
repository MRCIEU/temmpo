# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0004_gene_synonym_for'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchresult',
            name='filename_stub',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='searchresult',
            name='has_completed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
