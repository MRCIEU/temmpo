# -*- coding: utf-8 -*-
""" TeMMPo test suite.

Test data used frequently in tests set up in the _set_up_test_search_criteria helper method.

        exposure term: Humans

            Parent terms:
                Organisms > Eukaryota > Animals > Chordata
                    > Vertebrates
                    > Mammals > Eutheria > Primates
                    > Haplorhini > Catarrhini > Hominidae

            2018 file locations
                mtrees2018.bin:3577:Humans;B01.050.150.900.649.313.988.400.112.400.400

            2015 file locations
                mtrees2015.bin:3566:Humans;B01.050.150.900.649.801.400.112.400.400

        mediator terms: Phenotype and descendent terms

            2018 file locations
                mtrees2015.bin:48876:Phenotype;G05.695
                mtrees2015.bin:48877:Ecotype;G05.695.200
                mtrees2015.bin:48878:Endophenotypes;G05.695.224
                mtrees2015.bin:48879:Gene-Environment Interaction;G05.695.337
                mtrees2015.bin:48880:Genetic Markers;G05.695.450
                mtrees2015.bin:48881:Genetic Pleiotropy;G05.695.550
                mtrees2015.bin:48882:Penetrance;G05.695.650
                mtrees2015.bin:48883:Serogroup;G05.695.825

            2015 file locations
                mtrees2018.bin:50634:Phenotype;G05.695
                mtrees2018.bin:50635:Ecotype;G05.695.200
                mtrees2018.bin:50636:Endophenotypes;G05.695.224
                mtrees2018.bin:50637:Gene-Environment Interaction;G05.695.337
                mtrees2018.bin:50638:Genetic Markers;G05.695.450
                mtrees2018.bin:50639:Genetic Pleiotropy;G05.695.550
                mtrees2018.bin:50640:Penetrance;G05.695.650
                mtrees2018.bin:50641:Serogroup;G05.695.825

        outcome terms: Apoptosis and descendent terms

            2018 file locations
                mtrees2018.bin:49778:Apoptosis;G04.146.160
                mtrees2018.bin:49780:Eryptosis;G04.146.160.295
                mtrees2018.bin:49781:Pyroptosis;G04.146.160.530

            2015 file locations
                mtrees2015.bin:48033:Apoptosis;G04.299.139.160
                mtrees2015.bin:48034:Anoikis;G04.299.139.160.060
"""

import json
import os
from datetime import datetime, timedelta
import glob

from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.utils import timezone

from browser.matching import _pubmed_readcitations  # perform_search
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene

from tests.base_test_case import BaseTestCase

BASE_DIR = os.path.dirname(__file__)
TEST_FILE = os.path.join(BASE_DIR, 'test-abstract.txt')
TEST_NO_MESH_SUBJECT_HEADINGS_FILE = os.path.join(BASE_DIR, 'pubmed-abstract.txt')
TEST_DOC_FILE = os.path.join(BASE_DIR, 'test.docx')
TEST_PUBMED_MEDLINE_ABSTRACTS = os.path.join(BASE_DIR, 'pubmed_result_100.txt')
TEST_OVID_MEDLINE_ABSTRACTS = os.path.join(BASE_DIR, 'ovid_result_100.txt')
TEST_BADLY_FORMATTED_FILE = os.path.join(BASE_DIR, 'test-badly-formatted-abstracts.txt')
PREVIOUS_TEST_YEAR = 2015
TEST_YEAR = 2018
TERM_MISSING_IN_CURRENT_RELEASE = 'Cell Physiological Processes' # mtrees2015.bin 47978:Cell Physiological Processes;G04.299
TERM_NAMES_MISSING_IN_CURRENT_RELEASE = 'Cell Aging, Cell Physiological Processes, G0 Phase'  # mtrees2015.bin 47980:Cell Aging;G04.299.119 - 48025:G0 Phase;G04.299.134.500.300
TERM_NEW_IN_CURRENT_RELEASE = 'Eutheria'


class SearchingTestCase(BaseTestCase):
    """Run tests for browsing the TeMMPo application."""

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def test_ovid_medline_matching(self):
        """Testing matching using OVID formatted abstracts file.

        Additional test data.

        gene: TRPC1
        citation file: test-abstract.txt

        Should find matches with both mediator term and gene only finds matches
        with the gene when the WEIGHTFILTER thresh hold is zero
        """
        search_criteria = self._set_up_test_search_criteria()
        original_gene_count = Gene.objects.filter(name="TRPC1").count()
        self.assertEqual(original_gene_count, 1)

        # Run the search, by posting filter and gene selection form
        self._login_user()
        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})

        # Verify expected content is on the gene and filter form page
        expected_text = ["Enter genes", "Filter", "e.g. Humans"]
        self._find_expected_content(path=path, msg_list=expected_text)

        # Filter by a genes
        response = self.client.post(path, {'genes': 'TRPC1,HTR1A'}, follow=True)

        # TODO Test filter by MeshTerm part of form

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'), 'r')
        test_results_abstract_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_abstracts.csv'), 'r')
        print("RESULTS ARE IN THE THESE FILES: ")
        print(test_results_edge_csv.name)
        print(test_results_abstract_csv.name)
        edge_file_lines = test_results_edge_csv.readlines()
        abstract_file_lines = test_results_abstract_csv.readlines()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[1].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 9)  # Expected 9 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        existing_gene_count = Gene.objects.filter(name="TRPC1").count()
        new_gene_count = Gene.objects.filter(name="HTR1A").count()
        self.assertEqual(existing_gene_count, original_gene_count)
        self.assertEqual(new_gene_count, 1)

    def _test_search_bulk_term_edit(self, abstract_file_path, file_format, search_url):
        """Upload file and try to bulk select mesh terms."""
        with open(abstract_file_path, 'r') as upload:
            response = self.client.post(search_url,
                                        {'abstracts_upload': upload,
                                         'file_format': file_format},
                                        follow=True)

            self.assertContains(response, "Select exposures")
            self.assertContains(response, "Bulk edit")
            search_criteria = SearchCriteria.objects.latest("created")
            self.assertEqual(search_criteria.exposure_terms.all().count(), 0)
            exposure_url = reverse('exposure_selector', kwargs={'pk': search_criteria.id})
            response = self.client.post(exposure_url,
                                        {"term_names": "Genetic Markers;Serogroup; Penetrance",
                                         "btn_submit": "replace"},
                                        follow=True)
            search_criteria.refresh_from_db()
            # NB: Only a limited set of mesh terms are available for testing, for speed purposes
            exposure_terms = search_criteria.exposure_terms.all()
            unique_exposure_terms = set(exposure_terms.values_list("term", flat=True))
            self.assertEqual(exposure_terms.count(), 4) # NB: Penetrance appears twice in this test mesh tree subset
            self.assertEqual(len(unique_exposure_terms), 3)
            self.assertNotContains(response, " could not be found")

    def test_ovid_search_bulk_term_edit(self):
        """Test Ovid MEDLINE formatted search and bulk edit style searching."""
        self._login_user()
        self._find_expected_content(path=reverse('search'),
                                    msg="Upload abstracts to search")
        self._find_expected_content(path=reverse("search_ovid_medline"),
                                    msg=u"Search Ovid MEDLINE® formatted abstracts")
        # Search Ovid MEDLINE® formatted abstracts
        self._test_search_bulk_term_edit(abstract_file_path=TEST_OVID_MEDLINE_ABSTRACTS,
                                         file_format=OVID,
                                         search_url=reverse('search_ovid_medline'))

    def test_pubmed_search_bulk_term_edit(self):
        """Test PubMed formatted search and bulk edit style searching."""
        self._login_user()

        self._find_expected_content(path=reverse('search'),
                                    msg="Upload abstracts to search")
        self._find_expected_content(path=reverse("search_pubmed"),
                                    msg=u"Search PubMed MEDLINE® formatted abstracts")
        # Search PubMed formatted abstracts
        self._test_search_bulk_term_edit(abstract_file_path=TEST_PUBMED_MEDLINE_ABSTRACTS,
                                         file_format=PUBMED,
                                         search_url=reverse('search_pubmed'))

    def test_ovid_medline_file_upload_validation(self):
        """Test form validation for Ovid MEDLINE formatted abstracts files."""
        self._login_user()
        search_path = reverse('search_ovid_medline')

        with open(TEST_NO_MESH_SUBJECT_HEADINGS_FILE, 'r') as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': OVID},
                                        follow=True)
            self.assertContains(response, "errorlist")
            self.assertContains(response, "does not appear to be a Ovid MEDLINE® formatted")

        with open(TEST_DOC_FILE, 'r') as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': OVID},
                                        follow=True)

            self.assertContains(response, "errorlist")
            self.assertContains(response, "is not an acceptable file type")

    def test_pubmed_medline_file_upload_validation(self):
        """Test form validation for PubMed formatted abstracts files."""
        self._login_user()
        search_path = reverse('search_pubmed')

        with open(TEST_NO_MESH_SUBJECT_HEADINGS_FILE, 'r') as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': PUBMED},
                                        follow=True)
            self.assertContains(response, "errorlist")
            self.assertContains(response, "does not appear to be a PubMed/MEDLINE® formatted")

        with open(TEST_DOC_FILE, 'r') as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': PUBMED},
                                        follow=True)

            self.assertContains(response, "errorlist")
            self.assertContains(response, "is not an acceptable file type")

    def test_pubmed_readcitations_parsing_bug(self):
        """Test to capture a specific bug in file formats."""
        citations = _pubmed_readcitations(TEST_BADLY_FORMATTED_FILE)
        self.assertEqual(type(citations), list)
        self.assertEqual(len(citations), 23)

    def _assert_toggle_selecting_child_terms(self, search_criteria):
        """Helper function to test form toggle selection of child MeshTerms."""
        self.assertEqual(search_criteria.exposure_terms.all().count(), 0)

        exposure_url = reverse('exposure_selector', kwargs={'pk': search_criteria.id})
        response = self.client.post(exposure_url,
                                    {"term_names": "Cell Line",
                                     "include_child_nodes": "undetermined",
                                     "btn_submit": "replace"},
                                    follow=True)
        search_criteria.refresh_from_db()
        self.assertEqual(search_criteria.exposure_terms.all().count(), 1)

        response = self.client.post(exposure_url,
                                    {"term_names": "Cell Line",
                                     "include_child_nodes": "down",
                                     "btn_submit": "replace"},
                                    follow=True)
        search_criteria.refresh_from_db()
        self.assertEqual(search_criteria.exposure_terms.all().count(), 30)

        # Clear existing terms
        search_criteria.exposure_terms.clear()
        response = self.client.post(exposure_url,
                                    {"term_tree_ids": "mtid_21072",
                                     "include_child_nodes": "undetermined",
                                     "btn_submit": "choose"},
                                    follow=True)
        search_criteria.refresh_from_db()
        self.assertEqual(search_criteria.exposure_terms.all().count(), 1)

        # Clear existing terms
        search_criteria.exposure_terms.clear()
        response = self.client.post(exposure_url,
                                    {"term_tree_ids": "mtid_21072",
                                     "include_child_nodes": "down",
                                     "btn_submit": "choose"},
                                    follow=True)
        search_criteria.refresh_from_db()
        self.assertEqual(search_criteria.exposure_terms.all().count(), 30)

    def test_toggling_child_term_selection_ovid(self):
        """Test form toggle selection of child MeshTerms when working with an Ovid MEDLINE formatted file."""
        self._login_user()
        with open(TEST_OVID_MEDLINE_ABSTRACTS, 'r') as upload:
            response = self.client.post(reverse('search_ovid_medline'),
                                        {'abstracts_upload': upload,
                                         'file_format': OVID},
                                        follow=True)

            search_criteria = SearchCriteria.objects.latest("created")
            self._assert_toggle_selecting_child_terms(search_criteria=search_criteria)

    def test_toggling_child_term_selection_pubmed(self):
        """Test form toggle selection of child MeshTerms when working with an PubMed formatted file."""
        self._login_user()
        with open(TEST_PUBMED_MEDLINE_ABSTRACTS, 'r') as upload:
            response = self.client.post(reverse('search_pubmed'),
                                        {'abstracts_upload': upload,
                                         'file_format': PUBMED},
                                        follow=True)

            search_criteria = SearchCriteria.objects.latest("created")
            self._assert_toggle_selecting_child_terms(search_criteria=search_criteria)

    def test_filter_form_rendering(self):
        """Ensure bug TMMA-243 does not re-appear."""
        search_criteria = self._set_up_test_search_criteria()
        self._login_user()
        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})
        response = self.client.get(path, follow=True)
        self.assertContains(response, "TRPC1", msg_prefix=response.content)
        self.assertNotContains(response, "Gene: TRPC1", msg_prefix=response.content)
        search_criteria.delete()

    def _set_up_test_search_criteria(self, year=None):
        if not year:
            year = TEST_YEAR
        test_file = open(TEST_FILE, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        exposure_terms = MeshTerm.objects.get(term="Humans", year=year).get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Apoptosis", year=year).get_descendants(include_self=True)
        gene = Gene.objects.get(name="TRPC1")

        search_criteria = SearchCriteria(upload=upload, mesh_terms_year_of_release=year)
        search_criteria.save()

        search_criteria.genes.add(gene)
        search_criteria.exposure_terms = exposure_terms
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()

        return search_criteria

    def test_reuse_search(self):
        """Test the reuse search functionality."""
        self._find_expected_content(path=reverse("reuse_search"), msg="login to use this tool")
        self._login_user()
        self._find_expected_content(path=reverse("reuse_search"), msg="Reuse an existing upload or search criteria")

        expected_empty_messages = ['No previously uploaded abstracts.', 'No saved search criteria.', ]
        self._find_expected_content(path=reverse("reuse_search"), msg_list=expected_empty_messages)
        search_criteria = self._set_up_test_search_criteria()
        expected_test_messages = ['data-criteria-id="%s"' % search_criteria.id, search_criteria.upload, ]
        self._find_expected_content(path=reverse("reuse_search"), msg_list=expected_test_messages)

    def test_reuse_upload(self):
        """Test the reuse upload functionality."""
        self._login_user()
        original_criteria = self._set_up_test_search_criteria()
        path = reverse('reuse_upload', kwargs={'pk': original_criteria.upload.id})
        self._find_expected_content(path, msg='Select exposures')
        recent_search_criteria = SearchCriteria.objects.latest('id')
        # Ensure a search criteria new object has been created.
        self.assertNotEquals(original_criteria.id, recent_search_criteria.id)
        # Ensure no terms settings were carried over
        self.assertEqual(recent_search_criteria.exposure_terms.all().count(), 0)
        self.assertEqual(recent_search_criteria.mediator_terms.all().count(), 0)
        self.assertEqual(recent_search_criteria.outcome_terms.all().count(), 0)
        self.assertEqual(recent_search_criteria.mesh_terms_year_of_release, TEST_YEAR)
        # Check associated with the same upload.
        self.assertEqual(original_criteria.upload, recent_search_criteria.upload)

    def test_edit_search(self):
        """Test the reuse search criteria functionality."""
        self._login_user()
        original_criteria = self._set_up_test_search_criteria()
        path = reverse('edit_search', kwargs={'pk': original_criteria.id})
        expected_test_messages = ('Select exposures', 'Current exposure terms', )
        self._find_expected_content(path, msg_list=expected_test_messages)
        recent_search_criteria = SearchCriteria.objects.latest('id')

        # Ensure a search criteria new object has been created.
        self.assertNotEquals(original_criteria.id, recent_search_criteria.id)

        # Ensure exact terms settings were carried over
        self.assertEqual(list(original_criteria.exposure_terms.values_list("id", flat=True)), list(recent_search_criteria.exposure_terms.values_list("id", flat=True)))
        self.assertEqual(list(original_criteria.mediator_terms.values_list("id", flat=True)), list(recent_search_criteria.mediator_terms.values_list("id", flat=True)))
        self.assertEqual(list(original_criteria.outcome_terms.values_list("id", flat=True)), list(recent_search_criteria.outcome_terms.values_list("id", flat=True)))

        # Check associated with the same upload.
        self.assertEqual(original_criteria.upload, recent_search_criteria.upload)

        # Ensure using the current test year
        self.assertEqual(recent_search_criteria.mesh_terms_year_of_release, TEST_YEAR)

    def test_edit_search_with_previous_release_year(self):
        """Test edit_search when mesh term release years change and terms require conversion."""
        self._login_user()
        original_criteria = self._set_up_test_search_criteria(year=PREVIOUS_TEST_YEAR)
        extra_terms = MeshTerm.objects.get(year=PREVIOUS_TEST_YEAR, term=TERM_MISSING_IN_CURRENT_RELEASE).get_descendants(include_self=True)
        for term in extra_terms:
            original_criteria.outcome_terms.add(term)
        path = reverse('edit_search', kwargs={'pk': original_criteria.id})
        expected_test_messages = ('Select exposures', 'Current exposure terms',
                                  'Converting search from MeshTerm Terms released in %s' % str(PREVIOUS_TEST_YEAR),
                                  'outcome term(s) could not be translated into current MeSH Term equivalents: ',
                                  TERM_NAMES_MISSING_IN_CURRENT_RELEASE,)
        self._find_expected_content(path, msg_list=expected_test_messages)
        recent_search_criteria = SearchCriteria.objects.latest('id')

        # Ensure a search criteria new object has been created.
        self.assertNotEquals(original_criteria.id, recent_search_criteria.id)

        # Ensure expected terms settings were carried over
        self.assertEqual(list(original_criteria.exposure_terms.values_list("term", flat=True)), list(recent_search_criteria.exposure_terms.values_list("term", flat=True)))
        original_mediators = list(original_criteria.mediator_terms.values_list("term", flat=True))
        recent_mediators = list(recent_search_criteria.mediator_terms.values_list("term", flat=True))
        self.assertEqual(set(original_mediators), set(recent_mediators))

        previous_outcomes = list(original_criteria.outcome_terms.values_list("term", flat=True))
        new_outcomes = list(recent_search_criteria.outcome_terms.values_list("term", flat=True))
        self.assertNotEqual(previous_outcomes, new_outcomes)
        self.assertIn(TERM_MISSING_IN_CURRENT_RELEASE, previous_outcomes)
        self.assertNotIn(TERM_MISSING_IN_CURRENT_RELEASE, new_outcomes)

        # Assert recent search is using terms from the current year
        self.assertFalse(recent_search_criteria.exposure_terms.filter(year=PREVIOUS_TEST_YEAR).exists())
        self.assertFalse(recent_search_criteria.mediator_terms.filter(year=PREVIOUS_TEST_YEAR).exists())
        self.assertFalse(recent_search_criteria.outcome_terms.filter(year=PREVIOUS_TEST_YEAR).exists())

        # Check associated with the same upload.
        self.assertEqual(original_criteria.upload, recent_search_criteria.upload)

        # Ensure using the current test year for new searches
        self.assertNotEqual(original_criteria.mesh_terms_year_of_release, recent_search_criteria.mesh_terms_year_of_release)
        self.assertEqual(recent_search_criteria.mesh_terms_year_of_release, TEST_YEAR)

    def test_edit_search_with_previous_release_year_no_change(self):
        """Test edit_search when mesh term release years change but not terms are changed."""
        self._login_user()
        original_criteria = self._set_up_test_search_criteria(year=PREVIOUS_TEST_YEAR)
        path = reverse('edit_search', kwargs={'pk': original_criteria.id})
        expected_test_messages = ('Select exposures', 'Current exposure terms',
                                  'Converting search from MeshTerm Terms released in %s' % str(PREVIOUS_TEST_YEAR),)
        unexpected_test_messages = ('could not be translated',)
        response = self.client.get(path, follow=True)
        for msg in expected_test_messages:
            self.assertContains(response, msg)
        for msg in unexpected_test_messages:
            self.assertNotContains(response, msg)

        recent_search_criteria = SearchCriteria.objects.latest('id')

        # Ensure expected terms settings were carried over
        original_exposures = set(list(original_criteria.exposure_terms.values_list("term", flat=True)))
        recent_exposures = set(list(recent_search_criteria.exposure_terms.values_list("term", flat=True)))
        self.assertEqual(original_exposures, recent_exposures)

        original_mediators = set(list(original_criteria.mediator_terms.values_list("term", flat=True)))
        recent_mediators = set(list(recent_search_criteria.mediator_terms.values_list("term", flat=True)))
        self.assertEqual(original_mediators, recent_mediators)

        previous_outcomes = set(list(original_criteria.outcome_terms.values_list("term", flat=True)))
        new_outcomes = set(list(recent_search_criteria.outcome_terms.values_list("term", flat=True)))
        self.assertEqual(previous_outcomes, new_outcomes)

        # Assert recent search is using terms from the current year
        self.assertFalse(recent_search_criteria.exposure_terms.filter(year=PREVIOUS_TEST_YEAR).exists())
        self.assertFalse(recent_search_criteria.mediator_terms.filter(year=PREVIOUS_TEST_YEAR).exists())
        self.assertFalse(recent_search_criteria.outcome_terms.filter(year=PREVIOUS_TEST_YEAR).exists())

        # Check associated with the same upload.
        self.assertEqual(original_criteria.upload, recent_search_criteria.upload)

        # Ensure using the current test year for new searches
        self.assertEqual(recent_search_criteria.mesh_terms_year_of_release, TEST_YEAR)

    def test_exposure_selector(self):
        """Basic test for rendering the exposure terms selector page."""
        search_criteria = self._set_up_test_search_criteria()
        path = reverse('exposure_selector', kwargs={'pk': search_criteria.pk})
        search_criteria.exposure_terms.clear()
        search_criteria.save()

        self.client.logout()
        self._find_expected_content(path, msg="login to use this tool")

        self._login_user()
        self._find_expected_content(path, msg_list=["Bulk edit", "Add", "Select descendent", ])

        search_criteria.exposure_terms = MeshTerm.objects.get(term="Animals", year=TEST_YEAR).get_descendants(include_self=True)
        search_criteria.save()
        self._find_expected_content(path, msg_list=["Current exposure terms", "Bulk edit",
                                                    "Replace", "Select descendent", "Animals", ])

    def test_mediator_selector(self):
        """Basic test for rendering the mediator terms selector page."""
        search_criteria = self._set_up_test_search_criteria()
        path = reverse('mediator_selector', kwargs={'pk': search_criteria.pk})
        search_criteria.mediator_terms.clear()
        search_criteria.save()

        self.client.logout()
        self._find_expected_content(path, msg="login to use this tool")

        self._login_user()
        self._find_expected_content(path, msg_list=["Bulk edit", "Add", "Select descendent",
                                                    "Save and choose more mediator terms",
                                                    "Save and move on to select outcomes"])

        search_criteria.mediator_terms = MeshTerm.objects.get(term="Phenotype", year=TEST_YEAR).get_descendants(include_self=True)
        search_criteria.save()
        self._find_expected_content(path, msg_list=["Current mediator terms", "Bulk edit",
                                                    "Replace", "Select descendent", "Phenotype",
                                                    "Save and choose more mediator terms",
                                                    "Save and move on to select outcomes"])

    def test_outcome_selector(self):
        """Basic test for rendering the outcome terms selector page."""
        search_criteria = self._set_up_test_search_criteria()
        path = reverse('outcome_selector', kwargs={'pk': search_criteria.pk})
        search_criteria.outcome_terms.clear()
        search_criteria.save()

        self.client.logout()
        self._find_expected_content(path, msg="login to use this tool")

        self._login_user()
        self._find_expected_content(path, msg_list=["Bulk edit", "Add", "Select descendent",
                                                    "Save and choose more outcome terms", ])

        search_criteria.outcome_terms = MeshTerm.objects.get(term="Apoptosis", year=TEST_YEAR).get_descendants(include_self=True)
        search_criteria.save()
        self._find_expected_content(path, msg_list=["Current outcome terms", "Bulk edit",
                                                    "Replace", "Select descendent", "Apoptosis",
                                                    "Save and choose more outcome terms",
                                                    "Save and move on to select Genes and Filters", ])

    def test_criteria(self):
        """Test rendering of the view of a SearchCriteria instance."""
        search_criteria = self._set_up_test_search_criteria()
        self.client.logout()
        path = reverse('criteria', kwargs={'pk': search_criteria.pk})
        self._find_expected_content(path, msg_list=["login to use this tool", ])
        self._login_user()
        self._find_expected_content(path, msg_list=["Humans", "Phenotype",
                                                    "Apoptosis", "TRPC1",
                                                    "test-abstract.txt", ])

    # TODO: Test results JSON exports
    # def test_json_data(self):
    #     pass

    # TODO: (TMMA-227) Test result count data
    # def test_count_data(self):
    #     pass

    # TODO: (TMMA-222) Test abstracts data
    # def test_abstracts_data(self):
    #     pass

    # Test JSON MeSH Term exports

    def test_json_mesh_term_export(self):
        """Test the MeshTerm JSON used in jsTree."""
        self._login_user()
        response = self.client.get(reverse('mesh_terms_as_json'), follow=True)
        self.assertTrue('"text": "%d"' % TEST_YEAR not in response.content)

        # Assert valid JSON
        current_year_mesh_terms = json.loads(response.content)
        # Assert contains the number of expected top level terms for TEST_YEAR.
        self.assertEqual(len(current_year_mesh_terms), 16)
        # Assert the year filter term is not returned as a root node term.
        found = [x for x in current_year_mesh_terms if x['text'] == str(TEST_YEAR)]
        self.assertEqual(found, [])
        # Assert a leaf term is where expected.
        # "pk": 223987,
        # "term": "Humans",
        # "tree_number": "B01.050.150.900.649.313.988.400.112.400.400",
        # "year": 2018,
        # "level": 12
        levels_indicies = (1, 0, 2, 1, 1, 3, 0, 6, 0, 0, 1)
        level_12_b_terms = current_year_mesh_terms
        for i in levels_indicies:
            level_12_b_terms = level_12_b_terms[i]['children']
        term = level_12_b_terms[1]['text']
        self.assertEqual(term, "Humans")

    def test_mesh_terms_search_json(self):
        """Test the MeshTerm JSON used in jsTree searches.

        Test year filter parent node is not return.
        """
        self._login_user()
        path = reverse('mesh_terms_search_json') + "?str=Cell"
        response = self.client.get(path, follow=True)
        year_jstree_id = "mtid_" + str(MeshTerm.objects.get(term=str(TEST_YEAR)).id)
        self.assertTrue(year_jstree_id not in response.content)

        # Assert valid JSON.
        assert(json.loads(response.content))
        # Assert IDs with mtid_ prefix for all instances of mesh terms with Cell in the name are found.
        self.assertTrue("mtid_21072" in response.content)  # 21072 Cell Line
        self.assertTrue("mtid_21082" in response.content)  # 21082, 21110  Cell Line, Tumor
        self.assertTrue("mtid_21110" in response.content)
        self.assertTrue("mtid_24271" in response.content)  # 24271 Cell Physiological Phenomena
        self.assertTrue("mtid_24335" in response.content)  # 24335 Cell Death

    def test_search_for_new_mesh_terms_json(self):
        """Test that terms only in the previous term release is not present in current searches."""
        self._login_user()
        path = "%s?str=%s" % (reverse('mesh_terms_search_json'), TERM_NEW_IN_CURRENT_RELEASE)
        response = self.client.get(path, follow=True)
        new_term_tree_id = "mtid_" + str(MeshTerm.objects.get(year=TEST_YEAR, term=str(TERM_NEW_IN_CURRENT_RELEASE)).id)
        self.assertIn(new_term_tree_id, response.content)

    def test_search_for_old_mesh_terms_json(self):
        """Test that terms only in the previous term release is not present in current searches."""
        self._login_user()
        path = "%s?str=%s" % (reverse('mesh_terms_search_json'), TERM_MISSING_IN_CURRENT_RELEASE)
        response = self.client.get(path, follow=True)
        missing_term_tree_id = "mtid_" + str(MeshTerm.objects.get(year=PREVIOUS_TEST_YEAR, term=str(TERM_MISSING_IN_CURRENT_RELEASE)).id)
        self.assertFalse(missing_term_tree_id in response.content)

    def test_mesh_terms_as_json_for_tree_population(self):
        """Test can retrieve JSON to top level items in the MeshTerm jsTree."""
        search_criteria = self._set_up_test_search_criteria()
        # Classification term ids for 2018 (TEST_YEAR)
        root_nodes = range(20955, 20971)
        root_nodes = ["mtid_" + str(x) for x in root_nodes]
        self.assertEqual(len(root_nodes), 16)
        term_type_to_expected_nodes = {'exposure': root_nodes,
                                       'mediator': root_nodes,
                                       'outcome': root_nodes, }
        # Test retrieve root nodes if no node is supplied on the query string.
        for type_key, examples in term_type_to_expected_nodes.iteritems():
            path = reverse("mesh_terms_as_json_for_criteria", kwargs={"pk": search_criteria.id, "type": type_key})
            self._find_expected_content(path, msg_list=examples, content_type="application/json")

        # TODO Expand jsTree testing - Should selected state (and undetermined - not currently enabled) be tested as well here?

    def test_mesh_terms_as_json_for_tree_population_sub_tree(self):
        """Test can retrieve JSON that represent the children of a specific MeshTerm jsTree node."""
        search_criteria = self._set_up_test_search_criteria()
        # Expand the 2018 25242 Anatomy node
        expanded_node_query_string = '?id=mtid_25242'
        # Anatomy, Artistic 25243
        # Anatomy, Comparative 25244
        # Anatomy, Cross-Sectional 25245
        # Anatomy, Regional 25247
        # Anatomy, Veterinary 25248
        # Cell Biology 25249
        # Embryology 25250
        # Histology 25252
        # Neuroanatomy 25256
        # Osteology 25257
        children_nodes = ('mtid_25243', 'mtid_25244', 'mtid_25245', 'mtid_25247', 'mtid_25248',
                          'mtid_25249', 'mtid_25250', 'mtid_25252', 'mtid_25256', 'mtid_25257', )
        term_type_to_expected_nodes = {'exposure': children_nodes,
                                       'mediator': children_nodes,
                                       'outcome': children_nodes, }
        for type_key, examples in term_type_to_expected_nodes.iteritems():
            path = reverse("mesh_terms_as_json_for_criteria", kwargs={"pk": search_criteria.id, "type": type_key}) + expanded_node_query_string
            self._find_expected_content(path, msg_list=examples, content_type="application/json")

        # TODO Expand jsTree testing - Should selected state (and undetermined - not currently enabled) be tested as well here?

    def test_search_results_deletion(self):
        """Test we can delete results and associated files """

        search_criteria = self._set_up_test_search_criteria()
        original_gene_count = Gene.objects.filter(name="TRPC1").count()
        self.assertEqual(original_gene_count, 1)

        # Run the search, by posting filter and gene selection form
        self._login_user()
        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})

        # Verify expected content is on the gene and filter form page
        expected_text = ["Enter genes", "Filter", "e.g. Humans"]
        self._find_expected_content(path=path, msg_list=expected_text)

        # Filter by a genes
        response = self.client.post(path, {'genes': 'TRPC1,HTR1A'}, follow=True)

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'), 'r')
        test_results_abstract_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_abstracts.csv'), 'r')
        edge_file_lines = test_results_edge_csv.readlines()
        abstract_file_lines = test_results_abstract_csv.readlines()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[1].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 9)  # Expected 9 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        # Go to results page
        response = self.client.get(reverse('results_listing'))

        # Check delete button
        self.assertContains(response, 'Delete', count=2)

        # Fake still processing, no button
        search_result = SearchResult.objects.all()[0]
        search_result.has_completed = False
        search_result.save()
        response = self.client.get(reverse('results_listing'))
        self.assertContains(response, 'Delete', count=1)
        self.assertContains(response, 'Processing', count=1)

        # Check failed job, delete button
        orig_date = search_result.started_processing
        time_in_past = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=3)
        search_result.started_processing = time_in_past
        search_result.save()

        response = self.client.get(reverse('results_listing'))
        self.assertContains(response, 'Delete', count=2)
        self.assertContains(response, 'Search failed', count=1)

        # Reset search results
        search_result.has_completed = True
        search_result.started_processing = orig_date
        search_result.save()

        # Test deletion
        # Get should show confirmation screen
        response = self.client.get(reverse('delete_data', kwargs={'pk': search_result.id}))
        self.assertContains(response, 'Please confirm the deletion of this search.')
        self.assertContains(response, 'is not used in any other search and will be deleted')

        # Do POST
        # This does the actual delete
        # Check models
        all_search_results_count = SearchResult.objects.all().count()
        all_search_criteria_count = SearchCriteria.objects.all().count()
        all_uploads_count = Upload.objects.all().count()
        self.assertEqual(all_search_results_count, 1)
        self.assertEqual(all_search_criteria_count, 1)
        self.assertEqual(all_uploads_count, 1)

        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id
        self.assertTrue(SearchResult.objects.filter(pk=search_result_id).exists())
        self.assertTrue(SearchCriteria.objects.filter(pk=search_criteria_id).exists())
        self.assertTrue(Upload.objects.filter(pk=upload_id).exists())
        upload_record = Upload.objects.get(pk=upload_id)

        # Check files...
        # Check abstract
        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        base_path = settings.MEDIA_ROOT + '/results/' + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 5)

        # DO deletion
        response = self.client.post(reverse('delete_data', kwargs={'pk': search_result.id}), follow=True)
        self.assertContains(response, 'Search results deleted', count=1)

        # Re-check models etc
        self.assertEqual((all_search_results_count - 1),  SearchResult.objects.all().count())
        self.assertEqual((all_search_criteria_count - 1),  SearchCriteria.objects.all().count())
        self.assertEqual((all_uploads_count - 1),  Upload.objects.all().count())

        self.assertFalse(SearchResult.objects.filter(pk=search_result_id).exists())
        self.assertFalse(SearchCriteria.objects.filter(pk=search_criteria_id).exists())
        self.assertFalse(Upload.objects.filter(pk=upload_id).exists())

        # Check files...
        self.assertFalse(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)

    def test_search_results_can_only_be_deleted_by_owner(self):
        """Test another user cannot delete someone else's files """

        search_criteria = self._set_up_test_search_criteria()
        original_gene_count = Gene.objects.filter(name="TRPC1").count()
        self.assertEqual(original_gene_count, 1)

        # Run the search, by posting filter and gene selection form
        self._login_user()
        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})

        # Verify expected content is on the gene and filter form page
        expected_text = ["Enter genes", "Filter", "e.g. Humans"]
        self._find_expected_content(path=path, msg_list=expected_text)

        # Filter by a genes
        response = self.client.post(path, {'genes': 'TRPC1,HTR1A'}, follow=True)

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'), 'r')
        test_results_abstract_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_abstracts.csv'), 'r')
        edge_file_lines = test_results_edge_csv.readlines()
        abstract_file_lines = test_results_abstract_csv.readlines()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[1].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 9)  # Expected 9 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        # Go to results page
        response = self.client.get(reverse('results_listing'))

        # Check delete button
        self.assertContains(response, 'Delete', count=2)

        # Log out user
        self._logout_user()

        # Log in new user
        self._login_second_user()

        # Check no delete button etc
        response = self.client.get(reverse('results_listing'))
        # Should only be one instance (the table heading)
        self.assertContains(response, 'Delete', count=1)

        # Test deletion
        # Should not be shown a confirmation screen
        response = self.client.get(reverse('delete_data', kwargs={'pk': search_result.id}))
        self.assertEqual(response.status_code, 403)
        # Shown not be ale to delete object either
        response = self.client.post(reverse('delete_data', kwargs={'pk': search_result.id}))
        self.assertEqual(response.status_code, 403)