# -*- coding: utf-8 -*-
"""Test displaying custom system message"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone

from browser.models import SearchCriteria, SearchResult, Upload, Message
from tests.base_test_case import BaseTestCase


class MessageTestCase(BaseTestCase):

    def setUp(self):
        super(MessageTestCase, self).setUp()
        self.msg = Message.objects.create(body="Testing 1, 2, 3", user=self.user, end=timezone.now() + timedelta(days=1))
        self.msg.save()
        self._login_user()

    def test_home_page_message_not_shown(self):
        """Test cannot view message on home page"""
        response = self.client.get(reverse("home"), follow=True)
        self.assertNotContains(response, self.msg.body)
        self._logout_user()
        self.assertNotContains(response, self.msg.body)

    def test_credits_page(self):
        """Test cannot view message on the credits page"""
        response = self.client.get(reverse("credits"), follow=True)
        self.assertNotContains(response, self.msg.body)
        self._logout_user()
        self.assertNotContains(response, self.msg.body)

    def test_help_page(self):
        """Test cannot view message on the help page"""
        response = self.client.get(reverse("help"), follow=True)
        self.assertNotContains(response, self.msg.body)
        self._logout_user()
        self.assertNotContains(response, self.msg.body)

    def test_search_page(self):
        """Test can view system message on the search page."""
        self._find_expected_content(path=reverse("search"), msg=self.msg.body)

    def test_results_listing_page(self):
        """Test can view the results listing page."""
        self._find_expected_content(path=reverse("results_listing"), msg=self.msg.body)

    # Additional features
    def test_register_page(self):
        """Test cannot see message on the register page."""
        self._logout_user()
        response = self.client.get(reverse("registration_register"), follow=True)
        self.assertNotContains(response, self.msg.body)

    def test_login_page(self):
        """Test cannot see message on the login page."""
        response = self.client.get("/login", follow=True)
        self.assertNotContains(response, self.msg.body)

    def test_logout_page(self):
        """Test cannot see message on the logoout page."""
        response = self.client.get("/logout", follow=True)
        self.assertNotContains(response, self.msg.body)

    def test_super_user_access_to_admin_page(self):
        """Test staff user can access to the Django admin area to add messages."""
        self._logout_user()
        self._login_super_user()
        self._find_expected_content('/admin/browser/message/', msg_list=["Django administration", "Select message to change", ])

    def test_cannot_see_disabled_msg(self):
        """Test can view system message on the search page."""
        response = self.client.get(reverse("search"), follow=True)
        self.assertContains(response, self.msg.body)
        self.msg.is_disabled = True
        self.msg.save()
        response = self.client.get(reverse("search"), follow=True)
        self.assertNotContains(response, self.msg.body)

    def test_cannot_see_expired_msg(self):
        """Test can view system message on the search page."""
        response = self.client.get(reverse("search"), follow=True)
        self.assertContains(response, self.msg.body)
        self.msg.end = timezone.now() - timedelta(seconds=5)
        self.msg.save()
        response = self.client.get(reverse("search"), follow=True)
        self.assertNotContains(response, self.msg.body)