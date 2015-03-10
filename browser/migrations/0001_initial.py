# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Abstract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('citation_id', models.IntegerField(verbose_name=b'Unique Identifier')),
                ('abstract', models.TextField(verbose_name=b'Abstract')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MeshTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=300)),
                ('parent_id', models.IntegerField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchCriteria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('exposure_terms', models.ManyToManyField(related_name='+', to='browser.MeshTerm', blank=True, help_text=b'Select one or more terms', null=True, verbose_name=b'exposure MeSH terms')),
                ('genes', models.ManyToManyField(help_text=b'Enter one or more gene symbol', related_name='+', null=True, to='browser.Gene', blank=True)),
                ('mediator_terms', models.ManyToManyField(related_name='+', to='browser.MeshTerm', blank=True, help_text=b'Select one or more terms', null=True, verbose_name=b'mediator MeSH terms')),
                ('outcome_terms', models.ManyToManyField(related_name='+', to='browser.MeshTerm', blank=True, help_text=b'Select one or more terms', null=True, verbose_name=b'outcome MeSH terms')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mesh_filter', models.CharField(max_length=300, null=True, verbose_name=b'MeSH filter', blank=True)),
                ('results', models.FileField(null=True, upload_to=b'', blank=True)),
                ('criteria', models.ForeignKey(to='browser.SearchCriteria')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('abstracts_upload', models.FileField(upload_to=b'')),
                ('user', models.ForeignKey(related_name='uploads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='searchcriteria',
            name='upload',
            field=models.ForeignKey(related_name='searches', to='browser.Upload'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='abstract',
            name='headings',
            field=models.ForeignKey(to='browser.MeshTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='abstract',
            name='upload',
            field=models.ForeignKey(related_name='abstracts', to='browser.Upload'),
            preserve_default=True,
        ),
    ]
