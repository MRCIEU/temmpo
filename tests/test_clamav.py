# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import os

import magic
from selenium.common.exceptions import WebDriverException

from django.conf import settings
from django.urls import reverse
from django.test import override_settings, tag

from browser.models import Upload
from tests.base_selenium_test_case import SeleniumBaseTestCase
from tests.test_uploads import TEST_BZ_PUB_MED_SMALL_ARCHIVE, TEST_GZIP_PUB_MED_SMALL_ARCHIVE, TEST_BZ_OVID_ARCHIVE, TEST_GZIP_OVID_ARCHIVE

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)

@tag('clamav')  # Only supported by Apache fronted tests runners
@tag('selenium-test')
@override_settings(CLAMD_ENABLED=True)
class ScanOnUploadInterface(SeleniumBaseTestCase):

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def _assert_file_upload(url, file_path):
        logger.debug('_assert_file_upload %s %s ' % (url, file_path))
        previous_upload_count = Upload.objects.all().count()
        self.driver.get("%s%s" % (self.live_server_url, url))
        self.driver.find_element_by_id("abstracts_upload").clear()
        self.driver.find_element_by_id("abstracts_upload").send_keys(file_path)
        self.assertEqual(Upload.objects.all().count(), previous_upload_count + 1)
        uploaded_file = Upload.objects.all().order_by("id").last().abstracts_upload.file
        mime_type = magic.from_buffer(uploaded_file.read(2048), mime=True)
        self.assertEqual(mime_type, "text/plain")


class ScanOnArchiveUploadTestCase(ScanOnUploadInterface):
    """Test ClamAV enabled with archive abstract files"""
    def test_upload_pub_med_bz_archive(self):
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=TEST_BZ_PUB_MED_SMALL_ARCHIVE)

    def test_upload_pub_med_gzip_archive(self):
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=TEST_GZIP_PUB_MED_SMALL_ARCHIVE)

    def test_upload_ovid_bz_archive(self):
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=TEST_BZ_OVID_ARCHIVE)

    def test_upload_ovid_gzip_archive(self):
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=TEST_GZIP_OVID_ARCHIVE)

        """TODO: Trigger virus scanner file uploads wit EICAR txt directly to model and via form."""


class ScanOnUploadTestCase(ScanOnUploadInterface):
    """Test ClamAV enabled with text abstract upload files"""
    # fixtures = []
    def test_upload_ovid_file(self):
        file_path = os.path.join(BASE_DIR, 'test-abstract-ovid-test-sample-5.txt')
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=file_path)

    def test_upload_pubmed_file(self):
        file_path = os.path.join(BASE_DIR, 'test-abstract-pubmed-1.txt')
        self._upload_file(url=reverse("search_ovid_medline"), file_path=file_path)

    #  TODO: Trigger virus scanner file uploads wit EICAR txt directly to model and via form.

