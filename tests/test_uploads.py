# -*- coding: utf-8 -*-
import logging
import os

import magic

from django.urls import reverse
from django.test import tag

from browser.models import Upload, OVID, PUBMED

from tests.base_test_case import BaseTestCase

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger(__name__)

# Valid archive uploads
TEST_BZ_PUB_MED_ARCHIVE = os.path.join(BASE_DIR, '10-40-56-prostatic_neoplasms.txt.bz2')
TEST_GZIP_PUB_MED_ARCHIVE = os.path.join(BASE_DIR, '10-40-56-prostatic_neoplasms.txt.gz')
TEST_BZ_PUB_MED_SMALL_ARCHIVE = os.path.join(BASE_DIR, 'pubmed_result_100.txt.bz2')
TEST_GZIP_PUB_MED_SMALL_ARCHIVE = os.path.join(BASE_DIR, 'pubmed_result_100.txt.gz')
TEST_BZ_OVID_ARCHIVE = os.path.join(BASE_DIR, 'ovid_result_100.txt.bz2')
TEST_GZIP_OVID_ARCHIVE = os.path.join(BASE_DIR, 'ovid_result_100.txt.gz')

TEST_PUBMED_WITHOUT_BLANK_LINE = os.path.join(BASE_DIR, 'test_pubmed_wihout_leading_blank_line.txt')

#Invalid file uploads
TEST_NO_MESH_SUBJECT_HEADINGS_FILE = os.path.join(BASE_DIR, 'no-mesh-terms-abstract.txt')
TEST_DOC_FILE = os.path.join(BASE_DIR, 'test.docx')

#Invalid archive uploads
TEST_BZ_ARCHIVE_BADLY_FORMATTED_FILE = os.path.join(BASE_DIR, 'no-mesh-terms-abstract-large.txt.bz2')
TEST_GZIP_ARCHIVE_BADLY_FORMATTED_FILE = os.path.join(BASE_DIR, 'no-mesh-terms-abstract-large.txt.gz')
TEST_BZ_DOC_ARCHIVE = os.path.join(BASE_DIR, 'test.docx.bz2')
TEST_GZIP_DOC_ARCHIVE = os.path.join(BASE_DIR, 'test.docx.gz')
TEST_ZIP_DOC_ARCHIVE = os.path.join(BASE_DIR, 'test.docx.zip')
TEST_ZIP_PUB_MED_SMALL_ARCHIVE = os.path.join(BASE_DIR, 'pubmed_result_100.txt.zip')
TEST_ZIP_OVID_SMALL_ARCHIVE = os.path.join(BASE_DIR, 'ovid_result_100.txt.zip')

class UploadTestCase(BaseTestCase):
    """Run tests for browsing the TeMMPo application."""

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def _assert_upload_is_invalid_file_type(self, upload_file, search_path):
        with open(upload_file, 'rb',) as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': PUBMED},
                                        follow=True,
                                        format='multipart')
            self.assertContains(response, "errorlist")
            self.assertContains(response, "is not an acceptable file type")

    def test_ovid_medline_file_upload_validation(self):
        """Test form validation for Ovid MEDLINE formatted abstracts files."""
        self._login_user()
        search_path = reverse('search_ovid_medline')

        with open(TEST_NO_MESH_SUBJECT_HEADINGS_FILE, 'rb',) as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': OVID},
                                        follow=True,
                                        format='multipart')
            self.assertContains(response, "errorlist")
            self.assertContains(response, "does not appear to be a Ovid MEDLINE® formatted")

        self._assert_upload_is_invalid_file_type(TEST_DOC_FILE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_GZIP_DOC_ARCHIVE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_BZ_DOC_ARCHIVE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_ZIP_DOC_ARCHIVE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_ZIP_OVID_SMALL_ARCHIVE, search_path)

    def test_pubmed_medline_file_upload_validation(self):
        """Test form validation for PubMed formatted abstracts files."""
        self._login_user()
        search_path = reverse('search_pubmed')

        with open(TEST_NO_MESH_SUBJECT_HEADINGS_FILE, 'rb',) as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': PUBMED},
                                        follow=True,
                                        format='multipart')
            self.assertContains(response, "errorlist")
            self.assertContains(response, "does not appear to be a PubMed/MEDLINE® formatted")

        self._assert_upload_is_invalid_file_type(TEST_DOC_FILE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_GZIP_DOC_ARCHIVE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_BZ_DOC_ARCHIVE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_ZIP_DOC_ARCHIVE, search_path)
        self._assert_upload_is_invalid_file_type(TEST_ZIP_PUB_MED_SMALL_ARCHIVE, search_path)

    # See @tag upload in matching for full search life cycle from small/large archive file to matching

    def _setup_file_upload_response(self, test_archive_file, search_path):
        """Defaults to using pub med formatted search form"""
        self._login_user()
        with open(test_archive_file, 'rb',) as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': PUBMED},
                                        follow=True,
                                        format='multipart')
        return response

    def _assert_file_is_uploaded_and_extracted_where_required(self, test_archive_file, search_path):
        """Is this test file an archive we can process?"""
        previous_upload_count = Upload.objects.all().count()
        response = self._setup_file_upload_response(test_archive_file, search_path)
        self.assertNotContains(response, "is not an acceptable file type")
        self.assertNotContains(response, "is not a plain text file")
        self.assertEqual(Upload.objects.all().count(), previous_upload_count + 1)
        upload = Upload.objects.all().order_by("id").last().abstracts_upload
        mime_type = magic.from_buffer(upload.file.read(1024), mime=True)
        self.assertEqual(mime_type, "text/plain")

    def test_bz2_pub_med_upload_is_allowable(self):
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_BZ_PUB_MED_ARCHIVE, reverse('search_pubmed'))

    def test_gzip_pub_med_upload_is_allowable(self):
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_GZIP_PUB_MED_ARCHIVE, reverse('search_pubmed'))

    @tag('mimetype')
    def test_small_bz2_pub_med_upload_is_allowable(self):
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_BZ_PUB_MED_SMALL_ARCHIVE, reverse('search_pubmed'))

    @tag('mimetype')
    def test_small_gzip_pub_med_upload_is_allowable(self):
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_GZIP_PUB_MED_SMALL_ARCHIVE, reverse('search_pubmed'))

    def test_bz2_ovid_upload_is_allowable(self):
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_BZ_OVID_ARCHIVE, reverse('search_ovid_medline'))

    def test_gzip_ovid_upload_is_allowable(self):
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_GZIP_OVID_ARCHIVE, reverse('search_ovid_medline'))

    def _assert_invalid_pub_med_archive_fail(self, test_archive_file):
        previous_upload_count = Upload.objects.all().count()
        response = self._setup_file_upload_response(test_archive_file, reverse('search_pubmed'))
        self.assertEqual(Upload.objects.all().count(), previous_upload_count)
        self.assertContains(response, "does not appear to be a PubMed/MEDLINE")
        self.assertNotContains(response, "is not an acceptable file type")
        self.assertNotContains(response, "is not a plain text file")

    def test_gzip_with_invalid_pub_med_file(self):
        self._assert_invalid_pub_med_archive_fail(TEST_GZIP_ARCHIVE_BADLY_FORMATTED_FILE)

    def test_bz_with_invalid_pub_med_file(self):
        self._assert_invalid_pub_med_archive_fail(TEST_BZ_ARCHIVE_BADLY_FORMATTED_FILE)

    def test_can_upload_pubmed_file_with_missing_initial_blank_line(self):
        """#TMMA-496: Investigate issue parsing PubMed abstract uploads"""
        self._assert_file_is_uploaded_and_extracted_where_required(TEST_PUBMED_WITHOUT_BLANK_LINE, reverse('search_pubmed'))
