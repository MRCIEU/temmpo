"""Test for import MeshTerm and Gene management commands using sample file snippets."""
from StringIO import StringIO
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from django.core.management import call_command
from django.test import TestCase

from browser.models import Gene, MeshTerm


class RunSearchManagementCommandTest(TestCase):
    """Test running the run_search management command incorrectly."""

    fixtures = ['mesh-terms-test-only.json', 'genes-test-only.json', ]

    def test_run_search_without_args(self):
        """Check command handles a lack of parameters."""
        out = StringIO()
        try:
            call_command('run_search', stdout=out)
            assert(False)
        except CommandError as e:
            self.assertIn('Error: too few arguments', str(e))

    def test_run_search_with_unknown_args(self):
        """Check command handles an unknown search results ID parameters."""
        out = StringIO()
        try:
            call_command('run_search', 777, stdout=out)
            assert(False)
        except ObjectDoesNotExist as e:
            self.assertIn('SearchResult matching query does not exist.', str(e))


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


class ImportMeshTermsManagementCommandTest(TestCase):
    """Test running the import_mesh_terms management command."""

    def test_import_mesh_terms_command_without_args(self):
        """Check command handles a lack of parameters."""
        out = StringIO()
        try:
            call_command('import_mesh_terms', stdout=out)
            assert(False)
        except CommandError as e:
            self.assertIn('Error: too few arguments', str(e))

    def test_import_mesh_terms_command_with_unknown_args(self):
        out = StringIO()
        try:
            call_command('import_mesh_terms', "made-up-file-path.txt", "1999", stdout=out)
            assert(False)
        except CommandError as e:
            self.assertIn('No such file or directory', str(e))

    def test_import_mesh_terms_command(self):
        out = StringIO()
        file_path = os.path.dirname(os.path.dirname(__file__)) + '/browser/fixtures/test_mesh_terms_file_a.txt'
        year = 2000
        call_command('import_mesh_terms', file_path, year, stdout=out)

        # Assert that expected terms have been imported.
        terms = MeshTerm.objects.all()
        self.assertEqual(terms.count(), 30)
        top_level_mesh_terms = list(MeshTerm.get_top_level_mesh_terms(year).values_list("term", flat=True))
        self.assertEqual(top_level_mesh_terms, ['Body Regions', 'Eukaryota', 'Bacterial Infections and Mycoses', ])

        # Ensure re-running the command does not duplicate terms.
        call_command('import_mesh_terms', file_path, year, stdout=out)
        terms = MeshTerm.objects.all()
        self.assertEqual(terms.count(), 30)

    def test_import_mesh_terms_command_for_multiple_releases(self):
        """Test running the import command for different years"""
        out = StringIO()
        file_path_suffix = os.path.dirname(os.path.dirname(__file__)) + '/browser/fixtures/test_mesh_terms_file_'
        year = 2015
        call_command('import_mesh_terms', file_path_suffix + "a.txt", year, stdout=out)
        year = 2018
        call_command('import_mesh_terms', file_path_suffix + "b.txt", year, stdout=out)

        ankels_found = MeshTerm.objects.filter(term="Ankle").count()
        self.assertEqual(ankels_found, 2)
        ankels_found = MeshTerm.objects.filter(term="Ankle", year=2018).count()
        self.assertEqual(ankels_found, 1)

        ankels_found = MeshTerm.objects.filter(term="Hemorrhagic Septicemia").count()
        self.assertEqual(ankels_found, 1)
        ankels_found = MeshTerm.objects.filter(term="Hemorrhagic Septicemia", year=2015).count()
        self.assertEqual(ankels_found, 1)
        ankels_found = MeshTerm.objects.filter(term="Hemorrhagic Septicemia", year=2018).count()
        self.assertEqual(ankels_found, 0)

        # Test changes between years