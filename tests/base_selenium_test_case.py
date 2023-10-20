# -*- coding: utf-8 -*-
"""Acceptance test helper using Django's StaticLiveServerTestCase test
case to combine Selenium and Chrome webdriver for headless browser tests.
"""
import logging
import time

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from browser.utils import delete_user_content

logger = logging.getLogger(__name__)

class SeleniumBaseTestCase(StaticLiveServerTestCase):
    """A base test case for Selenium, providing helper methods."""

    @classmethod
    def setUpClass(cls):
        super(SeleniumBaseTestCase, cls).setUpClass()
        cls.display = Display(visible=0, size=(1920, 1080))
        cls.display.start()
        # ref: https://github.com/SeleniumHQ/selenium/issues/12746
        service = webdriver.ChromeService(executable_path="../../bin/chromedriver")
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        cls.display.stop()
        super(SeleniumBaseTestCase, cls).tearDownClass()

    def sel_open(self, url):
        """Universal helper functions."""
        self.driver.get("%s%s" % (self.live_server_url, url))
        time.sleep(3)

    # def sel_find_by_css(self, css):
    #     return self.driver.find_element(By.CSS_SELECTOR, css)

    # def sel_find_by_id(self, element_id):
    #     return self.driver.find_element(By.ID, element_id)

    # def sel_find_by_tag(self, element_tag):
    #     return self.driver.find_element_by_tag_name(element_tag)

    def login_user(self, user, password):
        self.sel_open(reverse('login'))

        self.driver.find_element(By.ID, "id_username").clear()
        self.driver.find_element(By.ID, "id_username").send_keys(user)

        self.driver.find_element(By.ID, "id_password").clear()
        self.driver.find_element(By.ID, "id_password").send_keys(password)

        self.driver.find_element(By.ID, "id_password").send_keys(Keys.RETURN)
        time.sleep(3)

    def setUp(self):
        username = 'may'
        email = 'may@example.com'
        password ='12345#abc'
        self.user = User.objects.create_user(id=999,
                                     username=username,
                                     email=email,
                                     password=password)
        self.login_user(user=username, password=password)
        time.sleep(3)

    def tearDown(self):
        """Clean up user content on the file system."""
        # self.create_debug_logs()
        delete_user_content(self.user)
        super(SeleniumBaseTestCase, self).tearDown()

    # def create_debug_logs(self, also_print=False):
    #     """Chrome console logs"""
    #     for entry in self.driver.get_log('browser'):
    #         logger.info(entry)
    #         if also_print:
    #             print(entry)

