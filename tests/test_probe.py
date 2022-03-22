# -*- coding: utf-8 -*-
from django.urls import reverse

from tests.base_test_case import BaseTestCase


class ProbeTestCase(BaseTestCase):

    def test_probe_compoenents(self):
        response = self.client.get(reverse("probe"), follow=True)
        self.assertContains(response, "Database connection")
        self.assertContains(response, "Database ORM")
        self.assertContains(response, "Email sending")
        self.assertContains(response, "Python version")


    def test_probe_alerts_up(self):
        response = self.client.get(reverse("probe"), follow=True)
        self.assertContains(response, "success", count=5)