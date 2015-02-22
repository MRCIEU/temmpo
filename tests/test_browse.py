""" TeMMPo test suite - browsing expected url paths
"""
import logging

from django.core.urlresolvers import reverse
from django.test import TestCase, Client

logger = logging.getLogger(__name__)
RESULT_HASH = "2020936a-9fe7-4047-bbca-6184780164a8"


class BrowsingTest(TestCase):
    """ Run simple tests for browsing the TeMMPo application
    """

    def setUp(self):
        self.browser = Client()
        super(BrowsingTest, self).setUp()

    def _find_expected_content(self, path="", url_path=None, msg=""):

        if url_path:
            path = reverse(url_path)

        response = self.browser.get(path)
        self.assertContains(response, msg,
                            msg_prefix="Expected %(msg)s at %(path)s" %
                            {'msg': msg, 'path': path})

    def test_about_page(self):
        """ Test can view the about page
        """

        self._find_expected_content(path="/", msg="About TeMMPo")

    def test_search_page(self):
        """ Test can view the search page
        """

        self._find_expected_content(path="/search", msg="Search")

    def test_results_page(self):
        """ Test can view the results page
        """

        self._find_expected_content(path="/results/" + RESULT_HASH,
                                    msg="Results")

    def test_results_listing_page(self):
        """ Test can view the results listing page
        """

        self._find_expected_content(path="/results", msg="My results")

    # def test_credits_page(self):
    #     """ Test can view the credits page
    #     """

    #     self._find_expected_content(path="/credits", msg="Credits")

    # Additional features

    # def test_register_page(self):
    #     """ Test can view the register page
    #     """

    #     self._find_expected_content(path="/register",
    #                                 msg="Create an account")

    # def test_login_page(self):
    #     """ Test can the sign in page
    #     """

    #     self._find_expected_content(path="/login", msg="Sign in")

    # def test_logout_page(self):
    #     """ Test can view the sign out page
    #     """

    #     self._find_expected_content(path="/logout", msg="You have siged out")

    # def test_results_archive(self):
    #     """
    #     """

    #     self._find_expected_content(path="/results/%s/archive" %
    #                                 RESULT_HASH, msg="Download")
