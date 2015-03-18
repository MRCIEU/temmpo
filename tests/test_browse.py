""" TeMMPo test suite - browsing expected url paths
"""
import logging

from django.core.urlresolvers import reverse
from django.test import TestCase, Client

logger = logging.getLogger(__name__)
RESULT_HASH = "2020936a-9fe7-4047-bbca-6184780164a8"
RESULT_ID = '1'


class BrowsingTest(TestCase):
    """ Run simple tests for browsing the TeMMPo application
    """

    def setUp(self):
        self.browser = Client()
        super(BrowsingTest, self).setUp()

    def _find_expected_content(self, path="", url_path=None, msg="", requires_login=False):

        if url_path:
            path = reverse(url_path)

        response = self.browser.get(path, follow=True)

        if requires_login:
            # TODO extend tests to cover logging in
            self.assertContains(response, 'Username', msg_prefix="Expected be redirected to the login page")
        else:
            self.assertContains(response, msg,
                            msg_prefix="Expected %(msg)s at %(path)s" %
                            {'msg': msg, 'path': path})

    def test_home_page(self):
        """ Test can view the home page
        """

        self._find_expected_content(path="/", msg="About TeMMPo")

    def test_credits_page(self):
        """ Test can view the credits page
        """

        self._find_expected_content(path="/credits/", msg="Credits")

    def test_search_page(self):
        """ Test can view the search page
        """

        self._find_expected_content(path="/search/", msg="Search", requires_login=True)

    def test_results_page(self):
        """ Test can view the results page
        """

        self._find_expected_content(path="/results/" + RESULT_ID,
                                    msg="Results",
                                    requires_login=True)

    def test_results_listing_page(self):
        """ Test can view the results listing page
        """

        self._find_expected_content(path="/results/", msg="My list", requires_login=True)

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

    #     self._find_expected_content(path="/logout",
    #                                 msg="You have signed out")

    # def test_results_archive(self):
    #     """
    #     """

    #     self._find_expected_content(path="/results/%s/archive" %
    #                                 RESULT_HASH, msg="Download")
