# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-09-22 13:01
from __future__ import unicode_literals

import browser.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    replaces = [('browser', '0001_initial'), ('browser', '0002_auto_20150318_1525'), ('browser', '0003_meshterm_tree_number'), ('browser', '0004_gene_synonym_for'), ('browser', '0005_auto_20150328_0831'), ('browser', '0006_auto_20150328_1228'), ('browser', '0007_auto_20150328_2227'), ('browser', '0008_auto_20150328_2331'), ('browser', '0009_auto_20150424_1728'), ('browser', '0010_auto_20150515_1342'), ('browser', '0011_auto_20151203_1814'), ('browser', '0012_auto_20180206_2354'), ('browser', '0013_auto_20180207_1514')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='MeshTerm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=300)),
                ('parent_id', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SearchCriteria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('exposure_terms', models.ManyToManyField(blank=True, help_text=b'Select one or more terms', null=True, related_name='+', to='browser.MeshTerm', verbose_name=b'exposure MeSH terms')),
                ('genes', models.ManyToManyField(blank=True, help_text=b'Enter one or more gene symbol', null=True, related_name='+', to='browser.Gene')),
                ('mediator_terms', models.ManyToManyField(blank=True, help_text=b'Select one or more terms', null=True, related_name='+', to='browser.MeshTerm', verbose_name=b'mediator MeSH terms')),
                ('outcome_terms', models.ManyToManyField(blank=True, help_text=b'Select one or more terms', null=True, related_name='+', to='browser.MeshTerm', verbose_name=b'outcome MeSH terms')),
            ],
        ),
        migrations.CreateModel(
            name='SearchResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mesh_filter', models.CharField(blank=True, max_length=300, null=True, verbose_name=b'MeSH filter')),
                ('results', models.FileField(blank=True, null=True, upload_to=b'')),
                ('criteria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_results', to='browser.SearchCriteria')),
                ('filename_stub', models.CharField(blank=True, max_length=100, null=True)),
                ('has_completed', models.BooleanField(default=False)),
                ('ended_processing', models.DateTimeField(blank=True, null=True)),
                ('started_processing', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abstracts_upload', models.FileField(upload_to=browser.models.get_user_upload_location)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to=settings.AUTH_USER_MODEL)),
                ('file_format', models.CharField(choices=[(b'ovid', b'Ovid'), (b'pubmed', b'PubMed')], default=b'ovid', max_length=6)),
            ],
        ),
        migrations.AddField(
            model_name='searchcriteria',
            name='upload',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='searches', to='browser.Upload'),
        ),
        migrations.RemoveField(
            model_name='meshterm',
            name='parent_id',
        ),
        migrations.AddField(
            model_name='meshterm',
            name='level',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='lft',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='browser.MeshTerm'),
        ),
        migrations.AddField(
            model_name='meshterm',
            name='rght',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meshterm',
            name='tree_id',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='name',
            field=models.CharField(blank=True, default=b'', help_text=b'Optional name for search criteria', max_length=300),
        ),
        migrations.AddField(
            model_name='meshterm',
            name='tree_number',
            field=models.CharField(max_length=250),
        ),
        migrations.AddField(
            model_name='gene',
            name='synonym_for',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='primary_gene', to='browser.Gene'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='exposure_terms',
            field=models.ManyToManyField(blank=True, help_text=b'Select one or more terms', null=True, related_name='sc_exposure', to='browser.MeshTerm', verbose_name=b'exposure MeSH terms'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='genes',
            field=models.ManyToManyField(blank=True, help_text=b'Enter one or more gene symbol', null=True, related_name='sc_gene', to='browser.Gene'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='mediator_terms',
            field=models.ManyToManyField(blank=True, help_text=b'Select one or more terms', null=True, related_name='sc_mediator', to='browser.MeshTerm', verbose_name=b'mediator MeSH terms'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='outcome_terms',
            field=models.ManyToManyField(blank=True, help_text=b'Select one or more terms', null=True, related_name='sc_outcome', to='browser.MeshTerm', verbose_name=b'outcome MeSH terms'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='exposure_terms',
            field=models.ManyToManyField(blank=True, help_text=b'Select one or more terms', related_name='sc_exposure', to='browser.MeshTerm', verbose_name=b'exposure MeSH terms'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='genes',
            field=models.ManyToManyField(blank=True, help_text=b'Enter one or more gene symbol', related_name='sc_gene', to='browser.Gene'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='mediator_terms',
            field=models.ManyToManyField(blank=True, help_text=b'Select one or more terms', related_name='sc_mediator', to='browser.MeshTerm', verbose_name=b'mediator MeSH terms'),
        ),
        migrations.AlterField(
            model_name='searchcriteria',
            name='outcome_terms',
            field=models.ManyToManyField(blank=True, help_text=b'Select one or more terms', related_name='sc_outcome', to='browser.MeshTerm', verbose_name=b'outcome MeSH terms'),
        ),
        migrations.AddField(
            model_name='meshterm',
            name='year',
            field=models.PositiveSmallIntegerField(db_index=True, default=2015),
        ),
        migrations.AddField(
            model_name='searchcriteria',
            name='mesh_terms_year_of_release',
            field=models.PositiveSmallIntegerField(default=2015),
        ),
    ]