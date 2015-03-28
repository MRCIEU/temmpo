# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0007_auto_20150328_2227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchresult',
            name='criteria',
            field=models.ForeignKey(related_name='search_results', to='browser.SearchCriteria'),
            preserve_default=True,
        ),
    ]
