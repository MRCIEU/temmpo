# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def populate_filename_stubs(apps, schema_editor):
    SearchResult = apps.get_model("browser", "SearchResult")
    for result in SearchResult.objects.all():
        result.filename_stub = "results_%s_%s_topresults" % (result.id, "human")
        result.save()


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0008_auto_20150328_2331'),
    ]

    operations = [
        migrations.RunPython(populate_filename_stubs, elidable=True),
    ]
