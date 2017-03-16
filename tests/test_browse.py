# -*- coding: utf-8 -*-
""" TeMMPo test suite
"""
# import datetime
import logging
import os


from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from browser.matching import _pubmed_readcitations  # perform_search
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED  # Gene,

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


class BrowsingTest(TestCase):
    """ Run simple tests for browsing the TeMMPo application
    """

    fixtures = ['mesh-terms-test-only.json', 'genes-test-only.json', ]

    def setUp(self):
        super(BrowsingTest, self).setUp()
        self.client = Client()
        self.user = User.objects.create_user(id=999,
                                             username='may',
                                             email='may@example.com',
                                             password='12345#abc')

    def _login_user(self):
        # self.client.logout()
        self.client.login(username='may', password='12345#abc')

    def _find_expected_content(self, path="", msg="", msg_list=None):
        response = self.client.get(path, follow=True)

        if not msg_list:
            msg_list = [msg, ]

        for text in msg_list:
            self.assertContains(response,
                                text,
                                msg_prefix="Expected %(msg)s at %(path)s" %
                                {'msg': text, 'path': path})

    def test_home_page(self):
        """ Test can view the home page
        """

        self._find_expected_content(path=reverse("home"), msg="About TeMMPo")

    def test_credits_page(self):
        """ Test can view the credits page
        """

        self._find_expected_content(path=reverse("credits"), msg="Credits")

    def test_search_page(self):
        """ Test can view the search page
        """
        self._find_expected_content(path=reverse("search"), msg="login to use this tool")
        self._find_expected_content(path=reverse("search_pubmed"), msg="login to use this tool")
        self._find_expected_content(path=reverse("search_ovid_medline"), msg="login to use this tool")
        self._login_user()
        self._find_expected_content(path=reverse("search"), msg="Upload abstracts to search")
        self._find_expected_content(path=reverse("search_pubmed"), msg=u"Search PubMed MEDLINE® formatted abstracts")
        self._find_expected_content(path=reverse("search_ovid_medline"), msg=u"Search Ovid MEDLINE® formatted abstracts")

    def test_results_page(self):
        """ Test can view the results page
        """
        path = reverse('results', kwargs={'pk': RESULT_ID})
        self._find_expected_content(path=path, msg="login to use this tool")
        self._login_user()
        # TODO add a mock search object
        # self._find_expected_content(path=path, msg='id="chart"')

    def test_results_listing_page(self):
        """ Test can view the results listing page
        """
        self._find_expected_content(path=reverse("results_listing"), msg="login to use this tool")
        self._login_user()
        self._find_expected_content(path=reverse("results_listing"), msg="My list")

    def test_ovid_medline_matching(self):
        """
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

        test_file = open(TEST_FILE, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        exposure_terms = MeshTerm.objects.get(term="Humans").get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype").get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Apoptosis").get_descendants(include_self=True)
        # genes = Gene.objects.filter(name="TRPC1")

        search_criteria = SearchCriteria(upload=upload)
        search_criteria.save()

        # search_criteria.genes = genes
        search_criteria.exposure_terms = exposure_terms
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()

        # search_result = SearchResult()
        # search_result.pk = 999
        # search_result.criteria = search_criteria
        # # search_result.started_processing = datetime.datetime.now()
        # # search_result.has_completed = False
        # search_result.save()

        # Run the search, by posting filter and gene selection form
        # TODO post mesh filter data
        # TODO split into separate tests - unit and integration
        self._login_user()
        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})
        response = self.client.post(path, {'genes': 'TRPC1'}, follow=True)

        # TODO: Split into pure integration and unit text version that does not use views
        # perform_search(search_result.id)

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'), 'r')
        print "RESULTS ARE IN THE THIS FILE: "
        print test_results_edge_csv.name
        self.assertEqual(len(test_results_edge_csv.readlines()), 2)  # Expected two matches
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

    def _test_search_bulk_term_edit(self, abstract_file_path, file_format, search_url):
        """Upload file and try to bulk select mesh terms"""
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
            self.assertEqual(search_criteria.exposure_terms.all().count(), 3)
            self.assertNotContains(response, " could not be found")

    def test_ovid_search_bulk_term_edit(self):
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
        self._login_user()

        self._find_expected_content(path=reverse('search'),
                                    msg="Upload abstracts to search")
        self._find_expected_content(path=reverse("search_pubmed"),
                                    msg=u"Search PubMed MEDLINE® formatted abstracts")
        # Search Ovid MEDLINE® formatted abstracts
        self._test_search_bulk_term_edit(abstract_file_path=TEST_PUBMED_MEDLINE_ABSTRACTS,
                                         file_format=PUBMED,
                                         search_url=reverse('search_pubmed'))

    # Additional features

    def test_register_page(self):
        """ Test can use the register page
        """
        self._find_expected_content(path=reverse("registration_register"),
                                    msg_list=["Register", "Password confirmation", ])

        response = self.client.post(reverse("registration_register"),
                                    {"username": "testuser1",
                                     "email": "bob@example.com",
                                     "password1": "THISISJUSTATEST",
                                     "password2": "THISISJUSTATEST"},
                                    follow=True)

        self.assertContains(response, "You registration is complete.", msg_prefix=response.content)

    def test_login_page(self):
        """ Test can view the sign in page
        """
        self._find_expected_content(path="/login/", msg="Login")

    def test_logout_page(self):
        """ Test logging out redirects to sign in page
        """
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)

        self._find_expected_content(path="/logout/",
                                    msg="Login")

    def test_ovid_medline_file_upload_validation(self):
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

    def test__pubmed_readcitations_parsing_bug(self):
        citations = _pubmed_readcitations(TEST_BADLY_FORMATTED_FILE)
        self.assertEqual(type(citations), list)
        self.assertEqual(len(citations), 23)

    # def test_results_archive(self):
    #     """
    #     """

    #     self._find_expected_content(path="/results/%s/archive" %
    #                                 RESULT_HASH, msg="Download")

# def test_gene_input # Can it handle new genes, unexpected spaces and other
# characters
