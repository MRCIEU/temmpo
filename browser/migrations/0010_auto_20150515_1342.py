# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import sys

from django.db import models, migrations

logger = logging.getLogger(__name__)

def populate_mesh_filter(apps, schema_editor):
    SearchResult = apps.get_model("browser", "SearchResult")

    # In the first instance Human text was used
    SearchResult.objects.filter(filename_stub__contains="_human_").update(mesh_filter="Human") 
    # Then the default filter was corrected
    SearchResult.objects.filter(filename_stub__contains="_humans_").update(mesh_filter="Humans") 


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0009_auto_20150424_1728'),
    ]

    operations = [
        migrations.RunPython(populate_mesh_filter, elidable=True),
    ]
