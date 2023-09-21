"""This management command is used as a one off setup for new projects to import and list of known gene names."""

from django.core.management.base import BaseCommand

from temmpo.prepopulate import pre_populate_genes


class Command(BaseCommand):
    """Django management command wrapper class."""

    help = 'Imports genes from the Homo_sapiens.gene_info fixture.'

    def handle(self, *args, **options):
        """Pass off to the helper command."""
        pre_populate_genes()
