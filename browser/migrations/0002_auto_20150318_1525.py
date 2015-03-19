# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import browser.models
import mptt.fields


class Migration(migrations.Migration):
    """ This migration will only work on an empty table """
    dependencies = [
        ('browser', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='meshterm',
            name='parent_id',
        ),
        migrations.AddField(
            model_name='meshterm',
            name='level',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='lft',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='browser.MeshTerm', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='rght',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='tree_id',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='name',
            field=models.CharField(default=b'', help_text=b'Optional name for search criteria', max_length=300, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='upload',
            name='abstracts_upload',
            field=models.FileField(upload_to=browser.models.get_user_upload_location),
            preserve_default=True,
        ),
    ]
