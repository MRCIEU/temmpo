# -*- coding: utf-8 -*-
"""Test view authorisation"""

from django.urls import reverse

from tests.base_test_case import BaseTestCase

RESULT_ID = '1'


class AccessTestCase(BaseTestCase):
    """Run simple tests for accessing the remainder of the TeMMPo application."""

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
        self._login_user()
        # Object does not exist
        self._find_expected_content(path=path, msg='Page not found', status_code=404)

    def test_results_bubble_chart_page(self):
        """Test can view the results page."""
        path = reverse('results_bubble', kwargs={'pk': RESULT_ID})
        self._find_expected_content(path=path, msg="login to use this tool")
        self._login_user()
        # Object does not exist
        self._find_expected_content(path=path, msg='Page not found', status_code=404)

    def test_results_listing_page(self):
        """Test can view the results listing page."""
        self._find_expected_content(path=reverse("results_listing"), msg="login to use this tool")
        self._login_user()
        self._find_expected_content(path=reverse("results_listing"), msg="My list")

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

        self.assertContains(response, "Your registration is complete.", msg_prefix=str(response.content))

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
                                                        "You don’t have permission to view or edit anything.", ])
    def test_super_access_to_admin(self):
        """Test super user have access to the Django admin."""
        self.client.logout()
        self._login_super_user()
        expected_dashboard = ["Site administration", "Genes", "Mesh terms",
                              "Search criterias", "Search results", "Uploads", ]
        self._find_expected_content('/admin', msg_list=expected_dashboard)

    def test_anon_access_to_message_queue_admin(self):
        """Test anon user needs to log in to access to the Django RQ dashboard."""
        self.client.logout()
        expected_dashboard = ["Django administration", "Log in", ]
        self._find_expected_content('/django-rq', msg_list=expected_dashboard)

    def test_user_access_to_message_queue_admin(self):
        """Test normal user needs to log in to access to the Django RQ dashboard."""
        expected_dashboard = ["Django administration", "Log in", ]
        self._find_expected_content('/django-rq', msg_list=expected_dashboard)

    def test_super_access_to_message_queue_admin(self):
        """Test super user have access to the Django RQ dashboard."""
        self.client.logout()
        self._login_super_user()
        expected_dashboard = ["RQ Queues", "Queued Jobs", ]
        self._find_expected_content('/django-rq', msg_list=expected_dashboard)
