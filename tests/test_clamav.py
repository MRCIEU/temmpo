# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import os
from time import sleep
from unittest import skip

import mimetypes
import requests
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from django.conf import settings
from django.urls import reverse
from django.test import override_settings, tag

from browser.models import Upload
from tests.base_selenium_test_case import SeleniumBaseTestCase
from tests.test_uploads import TEST_BZ_PUB_MED_SMALL_ARCHIVE, TEST_GZIP_PUB_MED_SMALL_ARCHIVE, TEST_BZ_OVID_ARCHIVE, TEST_GZIP_OVID_ARCHIVE

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
VIRUS_TXT_FILE_URL = "https://secure.eicar.org/eicar.com.txt"
VIRUS_ZIP_FILE_URL = "https://secure.eicar.org/eicar_com.zip"
VIRUS_DEEP_ZIP_FILE_URL = "https://secure.eicar.org/eicarcom2.zip"


@tag('clamav', 'selenium-test')
class ScanOnUploadInterface(SeleniumBaseTestCase):

    fixtures = ['test_searching_mesh_terms.json']

    def _upload_file(self, url, file_path):
        self.driver.get("%s%s" % (self.live_server_url, url))
        self.driver.find_element(By.ID, "id_abstracts_upload").send_keys(file_path)
        self.driver.find_element(By.ID, "upload_button").click()
        WebDriverWait(self.driver, timeout=30, poll_frequency=0.5).until(lambda x: x.find_element(By.ID, "id_include_child_nodes_1"))

    def _assert_file_upload(self, url, file_path):
        logger.debug('_assert_file_upload %s %s ' % (url, file_path))
        previous_upload_count = Upload.objects.all().count()
        self._upload_file(url, file_path)
        self.assertEqual(Upload.objects.all().count(), previous_upload_count + 1)
        uploaded_file_path = Upload.objects.all().order_by("id").last().abstracts_upload.path
        mime_type = mimetypes.guess_type(uploaded_file_path)
        self.assertEqual(mime_type[0], "text/plain")

    def _assert_virus_scanning(self, upload_url, virus_file_url):
        file_path = BASE_DIR + "/test_virus_file"
        response = requests.get(virus_file_url)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        previous_upload_count = Upload.objects.all().count()
        self._upload_file(upload_url, file_path)

        # Verify no new Upload objects were created.
        self.assertEqual(Upload.objects.all().count(), previous_upload_count)
        # Assert reason for lack of upload
        self.assertTrue("File is infected with malware" in self.driver.page_source, msg=self.driver.page_source)

        #  delete virus file
        os.remove(file_path)


class ScanOnArchiveUploadTestCase(ScanOnUploadInterface):
    """Test ClamAV enabled with archive abstract files"""

    @tag('upload')
    def test_upload_pub_med_bz_archive(self):
        self._assert_file_upload(url=reverse("search_pubmed"), file_path=TEST_BZ_PUB_MED_SMALL_ARCHIVE)

    @tag('upload')
    def test_upload_pub_med_gzip_archive(self):
        self._assert_file_upload(url=reverse("search_pubmed"), file_path=TEST_GZIP_PUB_MED_SMALL_ARCHIVE)

    @tag('upload')
    def test_upload_ovid_bz_archive(self):
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=TEST_BZ_OVID_ARCHIVE)

    @tag('upload')
    def test_upload_ovid_gzip_archive(self):
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=TEST_GZIP_OVID_ARCHIVE)

    @tag('upload')
    def test_upload_sample_a_pub_med_gzip_archive(self):
        abstract_file_path = os.path.join(BASE_DIR, "08-15-08-insulin-may-27-2019.txt.gz")
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=abstract_file_path)

    @tag('upload')
    def test_upload_sample_b_ovid_bz_archive(self):
        abstract_file_path = os.path.join(BASE_DIR, "07-32-54-exercise-inflamm-breast-cancer-may-3-2019-expanded-terms.txt.gz")
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=abstract_file_path)

    @tag('scanning')
    def test_scanning_ovid_zip_files(self):
        "Trigger virus scanner file uploads with EICAR zip with OVID upload form."
        self._assert_virus_scanning(reverse("search_ovid_medline"), VIRUS_ZIP_FILE_URL)

    @tag('scanning')
    def test_scanning_ovid_deep_zip_files(self):
        "Trigger virus scanner file uploads with EICAR deep zip with OVID upload form."
        self._assert_virus_scanning(reverse("search_ovid_medline"), VIRUS_DEEP_ZIP_FILE_URL)

    @tag('scanning')
    def test_scanning_pubmed_zip_files(self):
        "Trigger virus scanner file uploads with EICAR zip with PubMed upload form."
        self._assert_virus_scanning(reverse("search_pubmed"), VIRUS_ZIP_FILE_URL)

    @tag('scanning')
    def test_scanning_oubmed_deep_zip_files(self):
        "Trigger virus scanner file uploads with EICAR deep zip with PubMed upload form."
        self._assert_virus_scanning(reverse("search_pubmed"), VIRUS_DEEP_ZIP_FILE_URL)


class ScanOnUploadTestCase(ScanOnUploadInterface):
    """Test ClamAV enabled with text abstract upload files"""

    @tag('upload')
    def test_upload_ovid_file(self):
        "Test can upload OVID abstract files"
        file_path = os.path.join(BASE_DIR, 'test-abstract-ovid-test-sample-5.txt')
        self._assert_file_upload(url=reverse("search_ovid_medline"), file_path=file_path)

    @tag('upload')
    def test_upload_pubmed_file(self):
        "Test can upload PubMed abstract files"
        file_path = os.path.join(BASE_DIR, 'test-abstract-pubmed-1.txt')
        self._assert_file_upload(url=reverse("search_pubmed"), file_path=file_path)

    @tag('scanning')
    def test_scanning_ovid_txt_files(self):
        "Trigger virus scanner file uploads with EICAR txt with OVID upload form."
        self._assert_virus_scanning(reverse("search_ovid_medline"), VIRUS_TXT_FILE_URL)

    @tag('scanning')
    def test_scanning_pubmed_txt_files(self):
        "Trigger virus scanner file uploads with EICAR txt with PubMed upload form."
        self._assert_virus_scanning(reverse("search_pubmed"), VIRUS_TXT_FILE_URL)
