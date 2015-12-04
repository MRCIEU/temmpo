# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0010_auto_20150515_1342'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='file_format',
            field=models.CharField(default=b'ovid', max_length=6, choices=[(b'ovid', b'Ovid'), (b'pubmed', b'PubMed')]),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='exposure_terms',
            field=models.ManyToManyField(help_text=b'Select one or more terms', related_name='sc_exposure', verbose_name=b'exposure MeSH terms', to='browser.MeshTerm', blank=True),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='genes',
            field=models.ManyToManyField(help_text=b'Enter one or more gene symbol', related_name='sc_gene', to='browser.Gene', blank=True),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='mediator_terms',
            field=models.ManyToManyField(help_text=b'Select one or more terms', related_name='sc_mediator', verbose_name=b'mediator MeSH terms', to='browser.MeshTerm', blank=True),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='outcome_terms',
            field=models.ManyToManyField(help_text=b'Select one or more terms', related_name='sc_outcome', verbose_name=b'outcome MeSH terms', to='browser.MeshTerm', blank=True),
        ),
    ]
