# -*- coding: utf-8 -*-
"""Acceptance test helper using Django's StaticLiveServerTestCase test
case to combine Selenium and Chrome webdriver for headless browser tests.
"""

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse


class SeleniumBaseTestCase(StaticLiveServerTestCase):
    """A base test case for Selenium, providing helper methods."""

    @classmethod
    def setUpClass(cls):
        super(SeleniumBaseTestCase, cls).setUpClass()
        cls.display = Display(visible=0, size=(1024, 768))
        cls.display.start()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(15)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        cls.display.stop()
        super(SeleniumBaseTestCase, cls).tearDownClass()

    def sel_open(self, url):
        """Universal helper functions."""
        self.driver.get("%s%s" % (self.live_server_url, url))
        self.driver.implicitly_wait(5)

    def sel_find_by_css(self, css):
        return self.driver.find_element_by_css_selector(css)

    def sel_find_by_id(self, element_id):
        return self.driver.find_element_by_id(element_id)

    def sel_find_by_tag(self, element_tag):
        return self.driver.find_element_by_tag_name(element_tag)

    def login_user(self, user, password):
        self.sel_open(reverse('login'))

        self.driver.find_element_by_id("id_username").clear()
        self.driver.find_element_by_id("id_username").send_keys(user)

        self.driver.find_element_by_id("id_password").clear()
        self.driver.find_element_by_id("id_password").send_keys(password)

        self.driver.find_element_by_id("id_password").send_keys(Keys.RETURN)
        self.driver.implicitly_wait(5)

    def setUp(self):
        username = 'may'
        email = 'may@example.com'
        password ='12345#abc'
        self.user = User.objects.create_user(id=999,
                                     username=username,
                                     email=email,
                                     password=password)
        self.login_user(user=username, password=password)
