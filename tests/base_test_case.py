# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase, Client

from browser.utils import delete_user_content

class BaseTestCase(TestCase):


    def setUp(self):
        """Override set up to create test users of each Django default role type."""
        super(BaseTestCase, self).setUp()
        self.client = Client()
        self.hcaptcha_response = "10000000-aaaa-bbbb-cccc-000000000001"
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
        self.second_user = User.objects.create_user(id=1002,
                                                    username='june',
                                                    email='june@example.com',
                                                    password='12345#abc')
        self.inactive_user = User.objects.create_user(id=1003,
                                                    username='lazy',
                                                    email='lazy@example.com',
                                                    password='12345#abc')
        self.inactive_user.is_active = False
        self.inactive_user.save()

    def tearDown(self):
        """Clean up user content on the file system."""
        users = (self.user, self.staff_user, self.super_user_user, self.inactive_user)
        for user in users:
            delete_user_content(user.id)
        super(BaseTestCase, self).tearDown()

    def _login_user(self):
        self.client.login(username='may', password='12345#abc')

    def _login_staff_user(self):
        self.client.login(username='staff', password='12345#abc')

    def _login_super_user(self):
        self.client.login(username='super', password='12345#abc')

    def _login_second_user(self):
        self.client.login(username='june', password='12345#abc')

    def _logout_user(self):
        self.client.logout()

    def _find_expected_content(self, path="", msg="", msg_list=None, status_code=200, content_type="text/html; charset=utf-8"):
        response = self.client.get(path, follow=True)

        if not msg_list:
            msg_list = [msg, ]

        for text in msg_list:
            if text == "Not found":
                print(str(response.content))
            self.assertContains(response,
                                text,
                                status_code=status_code,
                                msg_prefix="Expected %(msg)s at %(path)s" %
                                {'msg': text, 'path': path})

        self.assertEqual(content_type, response['Content-Type'])