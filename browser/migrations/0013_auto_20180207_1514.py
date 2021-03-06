# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-07 15:14
from __future__ import unicode_literals
import logging

from django.db import migrations

from browser.models import MeshTerm

logger = logging.getLogger(__name__)

def filter_terms_by_year(apps, schema_editor):
    """."""
    logger.debug("Before migration - root nodes")
    logger.debug(MeshTerm.objects.root_nodes())
    root_nodes = MeshTerm.objects.root_nodes().exclude(tree_number="N/A")
    if root_nodes:
        year = 2015
        year_term = MeshTerm.objects.create(term=str(year), tree_number="N/A", year=year)
        for node in root_nodes:
            node.parent = year_term
            node.save()
    else:
        logger.debug("Found data that has already been migrated.")

    logger.debug("After migration - root nodes")
    logger.debug(MeshTerm.objects.root_nodes())


class Migration(migrations.Migration):
    """Create a data migration to restructure to be filtered by years."""
    dependencies = [('browser', '0012_auto_20180206_2354'), ]

    operations = [migrations.RunPython(filter_terms_by_year), ]
