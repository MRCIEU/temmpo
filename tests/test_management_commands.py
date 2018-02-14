"""Test for import MeshTerm and Gene management commands using sample file snippets."""
from io import StringIO
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from django.core.management import call_command
from django.test import TestCase

from browser.models import Gene


class RunSearchManagementCommandTest(TestCase):
    """Test running the run_search management command."""

    fixtures = ['mesh-terms-test-only.json', 'genes-test-only.json', ]

    def test_run_search_without_args(self):
        """Check command handles a lack of parameters."""
        out = StringIO()
        try:
            call_command('run_search', stdout=out)
        except CommandError as e:
            self.assertIn('Error: too few arguments', e)

    def test_run_search_with_unknown_args(self):
        """Check command handles an unknown search results ID parameters."""
        out = StringIO()
        try:
            call_command('run_search', 777, stdout=out)
        except ObjectDoesNotExist as e:
            self.assertIn('SearchResult matching query does not exist.', e)

    # TODO: Expand test for run_search management command,
    # def test_run_search_without_args(self):
    #     """Does command complain about a lack of parameters"""
    #     out = StringIO()
    #     call_command('run_search', stdout=out)
    #     self.assertIn('Must provide an id', out.getvalue())


class ImportGenesManagementCommandTest(TestCase):
    """Test running the import genes command."""

    def test_import_genes_command_output(self):
        """Test running the command against a sample gene info file.  NB: ACAT is referenced twice as a synonym."""
        test_file = os.path.dirname(os.path.dirname(__file__)) + '/browser/fixtures/test_gene_import_file.txt'
        expected_names = ['A1B', 'A1BG', 'ABG', 'ACAT', 'ACAT1', 'ACAT2', 'CE-1', 'CEH', 'CES1', 'CES2',
                          'GAB', 'HMSE', 'HMSE1', 'HYST2477', 'MAT', 'PCE-1', 'REH', 'SES1', 'T2', 'TGH', 'THIL', 'hCE-1', ]

        with self.settings(GENE_FILE_LOCATION=test_file):
            out = StringIO()
            call_command('import_genes', stdout=out)
            gene_count = Gene.objects.all().count()
            self.assertEqual(gene_count, len(expected_names))
            names = sorted(list(Gene.objects.all().values_list('name', flat=True)))
            self.assertEqual(names, expected_names)


# TODO: TMMA-131 Add test for importing MeSH Terms.
# class ImportMeshTermsManagementCommandTest(TestCase):
    # """Test running the import_mesh_terms management command."""
    # def test_import_mesh_terms_command_output(self):
    #     """."""
    #     out = StringIO()
    #     call_command('import_mesh_terms', stdout=out)
