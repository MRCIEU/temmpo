# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0005_auto_20150328_0831'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchcriteria',
            name='exposure_terms',
            field=models.ManyToManyField(related_name='sc_exposure', to='browser.MeshTerm', blank=True, help_text=b'Select one or more terms', null=True, verbose_name=b'exposure MeSH terms'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='genes',
            field=models.ManyToManyField(help_text=b'Enter one or more gene symbol', related_name='sc_gene', null=True, to='browser.Gene', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='mediator_terms',
            field=models.ManyToManyField(related_name='sc_mediator', to='browser.MeshTerm', blank=True, help_text=b'Select one or more terms', null=True, verbose_name=b'mediator MeSH terms'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='outcome_terms',
            field=models.ManyToManyField(related_name='sc_outcome', to='browser.MeshTerm', blank=True, help_text=b'Select one or more terms', null=True, verbose_name=b'outcome MeSH terms'),
            preserve_default=True,
        ),
    ]
