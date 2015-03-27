# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0003_meshterm_tree_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='gene',
            name='synonym_for',
            field=models.ForeignKey(related_name='primary_gene', blank=True, to='browser.Gene', null=True),
            preserve_default=True,
        ),
    ]
