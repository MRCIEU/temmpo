# -*- coding: utf-8 -*-
""" TeMMPo test suite.
"""
import json
import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from browser.matching import _pubmed_readcitations  # perform_search
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene

logger = logging.getLogger(__name__)
RESULT_HASH = "2020936a-9fe7-4047-bbca-6184780164a8"
RESULT_ID = '1'

BASE_DIR = os.path.dirname(__file__)
TEST_FILE = os.path.join(BASE_DIR, 'test-abstract.txt')
TEST_NO_MESH_SUBJECT_HEADINGS_FILE = os.path.join(BASE_DIR, 'pubmed-abstract.txt')
TEST_DOC_FILE = os.path.join(BASE_DIR, 'test.docx')
TEST_PUBMED_MEDLINE_ABSTRACTS = os.path.join(BASE_DIR, 'pubmed_result_100.txt')
TEST_OVID_MEDLINE_ABSTRACTS = os.path.join(BASE_DIR, 'ovid_result_100.txt')
TEST_BADLY_FORMATTED_FILE = os.path.join(BASE_DIR, 'test-badly-formatted-abstracts.txt')
PREVIOUS_TEST_YEAR = 2015
TEST_YEAR = 2018


class BrowsingTest(TestCase):
    """Run simple tests for browsing the TeMMPo application."""

    fixtures = ['mesh_terms_2015_2018.json', 'genes-test-only.json', ]  # ['mesh-terms-test-only.json', 'genes-test-only.json', 'mesh-terms-test-pevious-year-only.json', ]

    def setUp(self):
        """Override set up to create test users of each Django default role type."""
        super(BrowsingTest, self).setUp()
        self.client = Client()
        self.user = User.objects.create_user(id=999,
                                             username='may',
                                             email='may@example.com',
                                             password='12345#abc')
        self.staff_user = User.objects.create_user(id=1000,
                                                   username='staff',
                                                   email='staff@example.com',
                                                   password='12345#abc',
                                                   is_staff=True)
        self.super_user_user = User.objects.create_superuser(id=1001,
                                                             username='super',
                                                             email='super@example.com',
                                                             password='12345#abc')

    def _login_user(self):
        self.client.login(username='may', password='12345#abc')

    def _login_staff_user(self):
        self.client.login(username='staff', password='12345#abc')

    def _login_super_user(self):
        self.client.login(username='super', password='12345#abc')

    def _find_expected_content(self, path="", msg="", msg_list=None, status_code=200, content_type="text/html; charset=utf-8"):
        response = self.client.get(path, follow=True)

        if not msg_list:
            msg_list = [msg, ]

        for text in msg_list:
            if text == "Not found":
                print response
            self.assertContains(response,
                                text,
                                status_code=status_code,
                                msg_prefix="Expected %(msg)s at %(path)s" %
                                {'msg': text, 'path': path})

        self.assertEqual(content_type, response['Content-Type'])

    def test_home_page(self):
        """Test can view the home page without logging in."""
        self.client.logout()
        self._find_expected_content(path=reverse("home"), msg="About TeMMPo")

    def test_credits_page(self):
        """Test can view the credits page without logging in."""
        self.client.logout()
        self._find_expected_content(path=reverse("credits"), msg_list=["Credits", "NLM", "Technologies", ])

    def test_help_page(self):
        """Test can view the help page without logging in."""
        self.client.logout()
        self._find_expected_content(path=reverse("help"), msg_list=["Help", "Genes and filter section", ])

    def test_search_page(self):
        """Test can view the search page."""
        self._find_expected_content(path=reverse("search"), msg="login to use this tool")
        self._find_expected_content(path=reverse("search_pubmed"), msg="login to use this tool")
        self._find_expected_content(path=reverse("search_ovid_medline"), msg="login to use this tool")
        self._login_user()
        self._find_expected_content(path=reverse("search"), msg="Upload abstracts to search")
        self._find_expected_content(path=reverse("search_pubmed"), msg=u"Search PubMed MEDLINE® formatted abstracts")
        self._find_expected_content(path=reverse("search_ovid_medline"), msg=u"Search Ovid MEDLINE® formatted abstracts")

    def test_results_page(self):
        """Test can view the results page."""
        path = reverse('results', kwargs={'pk': RESULT_ID})
        self._find_expected_content(path=path, msg="login to use this tool")
        # TODO Add results rendering tests
        self._login_user()
        self._find_expected_content(path=path, msg='Page not found', status_code=404)

    def test_results_listing_page(self):
        """Test can view the results listing page."""
        self._find_expected_content(path=reverse("results_listing"), msg="login to use this tool")
        self._login_user()
        self._find_expected_content(path=reverse("results_listing"), msg="My list")

    def test_ovid_medline_matching(self):
        """Testing matching using OVID formatted abstracts file.

        Mesh terms

        exposure: Humans    (B01.050.150.900.649.801.400.112.400.400 Organisms >
         Eukaryota > Animals > Chordata > Vertebrates > Mammals > Primates >
         Haplorhini > Catarrhini > Hominidae)

        mediator: Phenotype (G05.695 Phenomena and Processes >
            Genetic Phenomena)

        outcome: Apoptosis (G04.299.139.160 Phenomena and Processes >
            Cell Physiological Phenomena > Cell Physiological Processes >
            Cell Death)

        gene: TRPC1

        citation file: test-abstract.txt
        or
        citation file: 13-53-45-22-39-12-citation_1-400.txt

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
        print "RESULTS ARE IN THE THES FILES: "
        print test_results_edge_csv.name
        print test_results_abstract_csv.name
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
            self.assertEqual(exposure_terms.count(), 5)
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

    # Additional features

    def test_register_page(self):
        """Test can use the register page."""
        self._find_expected_content(path=reverse("registration_register"),
                                    msg_list=["Register", "Password confirmation", ])

        response = self.client.post(reverse("registration_register"),
                                    {"username": "testuser1",
                                     "email": "bob@example.com",
                                     "password1": "THISISJUSTATEST",
                                     "password2": "THISISJUSTATEST"},
                                    follow=True)

        self.assertContains(response, "Your registration is complete.", msg_prefix=response.content)

    def test_login_page(self):
        """Test can view the sign in page."""
        self._find_expected_content(path="/login/", msg_list=["Login", "login to use this tool", ])

    def test_logout_page(self):
        """Test logging out redirects to sign in page."""
        self._login_user()
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)

        self._find_expected_content(path="/logout/",
                                    msg="Login")

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
                                    {"term_tree_ids": "mtid_222259",
                                     "include_child_nodes": "undetermined",
                                     "btn_submit": "choose"},
                                    follow=True)
        search_criteria.refresh_from_db()
        self.assertEqual(search_criteria.exposure_terms.all().count(), 1)

        # Clear existing terms
        search_criteria.exposure_terms.clear()
        response = self.client.post(exposure_url,
                                    {"term_tree_ids": "mtid_222259",
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
        extra_terms = MeshTerm.objects.get(year=PREVIOUS_TEST_YEAR, term="Cell Physiological Processes").get_descendants(include_self=True)
        for term in extra_terms:
            original_criteria.outcome_terms.add(term)
        path = reverse('edit_search', kwargs={'pk': original_criteria.id})
        expected_test_messages = ('Select exposures', 'Current exposure terms',
                                  'Converting search from MeshTerm Terms released in %s' % str(PREVIOUS_TEST_YEAR),
                                  'could not be translated',)
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
        self.assertIn("Cell Physiological Processes", previous_outcomes)
        self.assertNotIn("Cell Physiological Processes", new_outcomes)

        # Assert recent search is using terms from the current year
        self.assertFalse(recent_search_criteria.exposure_terms.filter(year=PREVIOUS_TEST_YEAR).exists())
        self.assertFalse(recent_search_criteria.mediator_terms.filter(year=PREVIOUS_TEST_YEAR).exists())
        self.assertFalse(recent_search_criteria.outcome_terms.filter(year=PREVIOUS_TEST_YEAR).exists())

        # Check associated with the same upload.
        self.assertEqual(original_criteria.upload, recent_search_criteria.upload)

        # Ensure using the current test year for new searches
        self.assertNotEqual(original_criteria.mesh_terms_year_of_release, recent_search_criteria.mesh_terms_year_of_release)
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
                                                    "Select these terms and choose more mediator terms",
                                                    "Select these terms and move on to select outcomes"])

        search_criteria.mediator_terms = MeshTerm.objects.get(term="Phenotype", year=TEST_YEAR).get_descendants(include_self=True)
        search_criteria.save()
        self._find_expected_content(path, msg_list=["Current mediator terms", "Bulk edit",
                                                    "Replace", "Select descendent", "Phenotype",
                                                    "Select these terms and choose more mediator terms",
                                                    "Select these terms and move on to select outcomes"])

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
                                                    "Select these terms and choose more outcome terms", ])

        search_criteria.outcome_terms = MeshTerm.objects.get(term="Apoptosis", year=TEST_YEAR).get_descendants(include_self=True)
        search_criteria.save()
        self._find_expected_content(path, msg_list=["Current outcome terms", "Bulk edit",
                                                    "Replace", "Select descendent", "Apoptosis",
                                                    "Select these terms and choose more outcome terms",
                                                    "Select these terms and move on to select Genes and Filters", ])

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

    # TODO: Test result count data
    # def test_count_data(self):
    #     pass

    # TODO: Test abstracts data
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
        self.assertTrue("mtid_222259" in response.content)  # 222259 Cell Line
        self.assertTrue("mtid_222297" in response.content)  # 1882  Cell Line, Tumor
        self.assertTrue("mtid_270123" in response.content)  # 270123 Cell Physiological Phenomena
        self.assertTrue("mtid_270187" in response.content)  # 270187 Cell Death

    def test_mesh_terms_as_json_for_tree_population(self):
        """Test can retrieve JSON to top level items in the MeshTerm jsTree."""
        search_criteria = self._set_up_test_search_criteria()
        # Classification term ids for 2018 (TEST_YEAR)
        root_nodes = range(220395, 220411)
        root_nodes = ["mtid_" + str(x) for x in root_nodes]
        self.assertEqual(len(root_nodes), 16)
        term_type_to_expected_nodes = {'exposure': root_nodes,
                                       'mediator': root_nodes,
                                       'outcome': root_nodes, }
        # Test retrieve root nodes if no node is supplied on the query string.
        for type_key, examples in term_type_to_expected_nodes.iteritems():
            path = reverse("mesh_terms_as_json_for_criteria", kwargs={"pk": search_criteria.id, "type": type_key})
            self._find_expected_content(path, msg_list=examples, content_type="application/json")

        # TODO Should undetermined/selected state be tested as well here.

    def test_mesh_terms_as_json_for_tree_population_sub_tree(self):
        """Test can retrieve JSON that represent the children of a specific MeshTerm jsTree node."""
        search_criteria = self._set_up_test_search_criteria()
        # Expand the 2018 272772 node
        expanded_node_query_string = '?id=mtid_272772'
        # Anatomy, Artistic 272773
        # Anatomy, Comparative 272774
        # Anatomy, Cross-Sectional 272775
        # Anatomy, Regional 272777
        # Anatomy, Veterinary 272778
        # Cell Biology 272779
        # Embryology 272780
        # Histology 272782
        # Neuroanatomy 272786
        # Osteology 272787
        children_nodes = ('mtid_272773', 'mtid_272774', 'mtid_272775', 'mtid_272777', 'mtid_272778',
                          'mtid_272779', 'mtid_272780', 'mtid_272782', 'mtid_272786', 'mtid_272787', )
        term_type_to_expected_nodes = {'exposure': children_nodes,
                                       'mediator': children_nodes,
                                       'outcome': children_nodes, }
        for type_key, examples in term_type_to_expected_nodes.iteritems():
            path = reverse("mesh_terms_as_json_for_criteria", kwargs={"pk": search_criteria.id, "type": type_key}) + expanded_node_query_string
            self._find_expected_content(path, msg_list=examples, content_type="application/json")

        # TODO Should undetermined/selected state be tested as well here.

    def test_anon_access_to_admin(self):
        """Test anonymous user does not have access to the Django admin."""
        self.client.logout()
        self._find_expected_content('/admin', msg_list=["Django administration", "Log in", ])
        self._login_user()
        self._find_expected_content('/admin', msg_list=["Django administration", "Log in", ])

    def test_staff_access_to_admin(self):
        """Test staff do not have access to the Django admin."""
        self.client.logout()
        self._find_expected_content('/admin', msg_list=["Django administration", "Log in", ])
        self._login_staff_user()
        self._find_expected_content('/admin', msg_list=["Site administration",
                                                        "You don't have permission to edit anything.", ])

    def test_super_access_to_admin(self):
        """Test super user have access to the Django admin."""
        self.client.logout()
        self._login_super_user()
        expected_dashboard = ["Site administration", "Genes", "Mesh terms",
                              "Search criterias", "Search results", "Uploads", ]
        self._find_expected_content('/admin', msg_list=expected_dashboard)

    # TODO: (Low priority) Give "search result" a better str representation
    # TODO: (Low priority) Pluralise "search criteria" change field representation my R/A for choice fields? esp for genes - can this be more like terms??
    # TODO: (Low priority) Maybe add year to str representation of mesh term
