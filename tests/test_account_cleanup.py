# -*- coding: utf-8 -*-
"""Test non mesh term functionality."""

import glob
import os
from datetime import datetime, timedelta

from django.utils import timezone
from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core import mail

from tests.base_test_case import BaseTestCase
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from browser.utils import user_clean_up


BASE_DIR = os.path.dirname(__file__)
TEST_FILE = os.path.join(BASE_DIR, 'test-abstract.txt')
TEST_NO_MESH_SUBJECT_HEADINGS_FILE = os.path.join(BASE_DIR, 'pubmed-abstract.txt')
TEST_DOC_FILE = os.path.join(BASE_DIR, 'test.docx')
TEST_PUBMED_MEDLINE_ABSTRACTS = os.path.join(BASE_DIR, 'pubmed_result_100.txt')
TEST_OVID_MEDLINE_ABSTRACTS = os.path.join(BASE_DIR, 'ovid_result_100.txt')
TEST_BADLY_FORMATTED_FILE = os.path.join(BASE_DIR, 'test-badly-formatted-abstracts.txt')
PREVIOUS_TEST_YEAR = 2015
TEST_YEAR = 2018
TERM_MISSING_IN_CURRENT_RELEASE = 'Cell Physiological Processes' # mtrees2015.bin 47978:Cell Physiological Processes;G04.299
TERM_NAMES_MISSING_IN_CURRENT_RELEASE = 'Cell Aging, Cell Physiological Processes, G0 Phase'  # mtrees2015.bin 47980:Cell Aging;G04.299.119 - 48025:G0 Phase;G04.299.134.500.300
TERM_NEW_IN_CURRENT_RELEASE = 'Eutheria'

class UserDeletionTest(BaseTestCase):

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def _set_up_test_search_criteria(self, year=None):
        if not year:
            year = TEST_YEAR
        test_file = open(TEST_FILE, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        exposure_terms = MeshTerm.objects.get(term="Humans", year=year).get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Apoptosis", year=year).get_descendants(include_self=True)
        gene = Gene.objects.get(name="TRPC1")

        search_criteria = SearchCriteria(upload=upload, mesh_terms_year_of_release=year)
        search_criteria.save()

        search_criteria.genes.add(gene)
        search_criteria.exposure_terms = exposure_terms
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()

        return search_criteria

    def test_user_deletion(self):
        """ Check that a user can close and delete their account """
        search_criteria = self._set_up_test_search_criteria()
        original_gene_count = Gene.objects.filter(name="TRPC1").count()
        self.assertEqual(original_gene_count, 1)

        # Run the search, by posting filter and gene selection form
        self._login_user()
        test_user = User.objects.get(id=999)

        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})

        # Verify expected content is on the gene and filter form page
        expected_text = ["Enter genes", "Filter", "e.g. Humans"]
        self._find_expected_content(path=path, msg_list=expected_text)

        # Filter by a genes
        response = self.client.post(path, {'genes': 'TRPC1,HTR1A'}, follow=True)

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'),
                                     'r')
        test_results_abstract_csv = open(
            os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_abstracts.csv'), 'r')
        edge_file_lines = test_results_edge_csv.readlines()
        abstract_file_lines = test_results_abstract_csv.readlines()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[1].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 9)  # Expected 9 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        # Go to results page
        response = self.client.get(reverse('results_listing'))

        # Check delete button
        self.assertContains(response, 'Delete', count=2)

        search_result = SearchResult.objects.all()[0]
        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id

        # Check files...
        # Check abstract
        upload_record = Upload.objects.get(pk=upload_id)

        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        base_path = settings.MEDIA_ROOT + '/results/' + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 5)

        # Check account page
        response = self.client.get(reverse('account'))
        self.assertContains(response, 'Manage your user account on TeMMPo')
        self.assertNotContains(response, 'Manage users')
        self.assertNotContains(response, 'Super user only')

        # Check deletion confirmation
        response = self.client.get(reverse('close_account', kwargs={'pk': test_user.id}))
        self.assertContains(response, 'This action cannot be undone and your account will be closed immediately.')

        # Check can't access another user's account
        response = self.client.get(reverse('close_account', kwargs={'pk': 1002}))
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse('close_account', kwargs={'pk': 1002}))
        self.assertEqual(response.status_code, 403)

        # Check can't delete if job is running
        search_result.has_completed = False
        search_result.save()
        response = self.client.get(reverse('results_listing'))
        self.assertContains(response, 'Delete', count=1)
        self.assertContains(response, 'Processing', count=1)
        response = self.client.get(reverse('close_account', kwargs={'pk': test_user.id}))
        self.assertContains(response, 'You have a search that is still running.')
        self.assertNotContains(response, 'Close my account and delete searches')
        response = self.client.post(reverse('close_account', kwargs={'pk': test_user.id}))
        self.assertEqual(response.status_code, 403)

        # Reset search
        search_result.has_completed = True
        search_result.save()

        # Do actual deletion, check clean up
        response = self.client.post(reverse('close_account', kwargs={'pk': test_user.id}), follow=True)
        self.assertContains(response, 'Your account has now been closed and any searches and uploads deleted.')

        # Check logout
        self.assertNotContains(response, 'User account')
        response = self.client.get(reverse('results_listing'), follow=True)
        self.assertContains(response, 'or login to use this tool')
        self.assertNotContains(response, 'My list')

        # Check records have gone
        self.assertFalse(SearchResult.objects.filter(pk=search_result_id).exists())
        self.assertFalse(SearchCriteria.objects.filter(pk=search_criteria_id).exists())
        self.assertFalse(Upload.objects.filter(pk=upload_id).exists())

        # Check files...
        self.assertFalse(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)

        # Check user record deleted
        self.assertFalse(User.objects.filter(pk=test_user.id).exists())

    def test_superuser_delete_user(self):
        """ Check that a superuser can delete users """
        search_criteria = self._set_up_test_search_criteria()
        original_gene_count = Gene.objects.filter(name="TRPC1").count()
        self.assertEqual(original_gene_count, 1)

        # Run the search, by posting filter and gene selection form
        self._login_user()
        test_user = User.objects.get(id=999)
        su_user = User.objects.get(id=1001)

        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})

        # Verify expected content is on the gene and filter form page
        expected_text = ["Enter genes", "Filter", "e.g. Humans"]
        self._find_expected_content(path=path, msg_list=expected_text)

        # Filter by a genes
        response = self.client.post(path, {'genes': 'TRPC1,HTR1A'}, follow=True)

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'),
                                     'r')
        test_results_abstract_csv = open(
            os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_abstracts.csv'), 'r')
        edge_file_lines = test_results_edge_csv.readlines()
        abstract_file_lines = test_results_abstract_csv.readlines()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[1].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 9)  # Expected 9 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        # Go to results page
        response = self.client.get(reverse('results_listing'))

        # Check delete button
        self.assertContains(response, 'Delete', count=2)

        search_result = SearchResult.objects.all()[0]
        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id

        # Check files...
        # Check abstract
        upload_record = Upload.objects.get(pk=upload_id)

        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        base_path = settings.MEDIA_ROOT + '/results/' + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 5)

        # Check can't access manage users page
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('delete_user', kwargs={'pk': test_user.id}))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('delete_user', kwargs={'pk': su_user.id}))
        self.assertEqual(response.status_code, 403)

        # Log out, superuser log in
        self._logout_user()
        self._login_super_user()

        # Access manage users page
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage users')
        self.assertContains(response, 'Delete user', count=4)

        # Check can't delete if searches running
        search_result.has_completed = False
        search_result.save()
        response = self.client.get(reverse('delete_user', kwargs={'pk': test_user.id}))
        self.assertContains(response, 'This user has a search that is still running')
        self.assertNotContains(response, 'Delete user (inc. their searches and uploads)')
        response = self.client.post(reverse('delete_user', kwargs={'pk': test_user.id}))
        self.assertEqual(response.status_code, 403)

        # Check can't delete yourself
        response = self.client.post(reverse('delete_user', kwargs={'pk': su_user.id}))
        self.assertEqual(response.status_code, 403)

        # Reset search
        search_result.has_completed = True
        search_result.save()

        # Delete other user
        response = self.client.get(reverse('delete_user', kwargs={'pk': test_user.id}))
        self.assertNotContains(response, 'This user has a search that is still running')
        self.assertContains(response, 'Delete user (inc. their searches and uploads)')
        response = self.client.post(reverse('delete_user', kwargs={'pk': test_user.id}), follow=True)
        self.assertContains(response, "User &#39;may&#39; deleted")

        # Check records have gone
        self.assertFalse(SearchResult.objects.filter(pk=search_result_id).exists())
        self.assertFalse(SearchCriteria.objects.filter(pk=search_criteria_id).exists())
        self.assertFalse(Upload.objects.filter(pk=upload_id).exists())

        # Check files...
        self.assertFalse(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)

        # Check user record deleted
        self.assertFalse(User.objects.filter(pk=test_user.id).exists())

        # Access manage users page
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage users')
        self.assertContains(response, 'Delete user', count=3)


class UserCleanUpManagementCommandTest(BaseTestCase):

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def setUp(self):
        super(UserCleanUpManagementCommandTest, self).setUp()
        self.year_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=370)
        self.last_login = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=settings.ACCOUNT_CLOSURE_WARNING)

        # Configure user who did not complete registration
        self.inactive_user.date_joined = self.year_ago
        self.inactive_user.save()

        # Configure registered user who hasn't logged in for a year
        self.user.date_joined = self.year_ago
        self.user.last_login = self.last_login
        self.user.save()

        # Give other users recent logins
        self.second_user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.second_user.save()
        self.staff_user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.staff_user.save()

        self.total_users = User.objects.all().count()

        # Clear mailbox
        mail.outbox = []

    def _set_up_test_search_criteria(self, year=None):
        if not year:
            year = TEST_YEAR
        test_file = open(TEST_FILE, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        exposure_terms = MeshTerm.objects.get(term="Humans", year=year).get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Apoptosis", year=year).get_descendants(include_self=True)
        gene = Gene.objects.get(name="TRPC1")

        search_criteria = SearchCriteria(upload=upload, mesh_terms_year_of_release=year)
        search_criteria.save()

        search_criteria.genes.add(gene)
        search_criteria.exposure_terms = exposure_terms
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()
        return search_criteria

    def test_initial_warning(self):
        """
        Check that a user is warned about account closure no matter when they signed up and none are deleted.
        This is needed because no account clean up was set up when the site went live.
        """

        user_clean_up(warn_historic=True)

        # Test that one message sent
        self.assertEqual(len(mail.outbox), 1)

        # Check subject line
        self.assertEqual(mail.outbox[0].subject, 'TeMMPo account closure warning')

        # Check recipient
        self.assertEqual(mail.outbox[0].to[0], self.user.email)

        # No users deleted
        self.assertEqual(self.total_users, User.objects.all().count())

    def test_warnings_only(self):
        """
        Test that if no_deletion flag is set then users are warned but no user is deleted even if they would normally
        """

        user_clean_up(no_deletion=True)

        # Test that one message sent
        self.assertEqual(len(mail.outbox), 1)

        # Check subject line
        self.assertEqual(mail.outbox[0].subject, 'TeMMPo account closure warning')

        # Check recipient
        self.assertEqual(mail.outbox[0].to[0], self.user.email)

        # No users deleted
        self.assertEqual(self.total_users, User.objects.all().count())

    def test_warning_sent(self):
        """
        Test that warning is sent to user
        """
        self.inactive_user.is_active = True
        self.inactive_user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.inactive_user.save()

        # # Configure registered user who hasn't logged in for a year
        # self.user.date_joined = self.year_ago
        # self.user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        # self.user.save()

        user_clean_up()

        # Test that one message sent
        self.assertEqual(len(mail.outbox), 1)

        # Check subject line
        self.assertEqual(mail.outbox[0].subject, 'TeMMPo account closure warning')

        # Check recipient
        self.assertEqual(mail.outbox[0].to[0], self.user.email)

        # No users deleted
        self.assertEqual(self.total_users, User.objects.all().count())

    def test_user_delete(self):
        """
        Test that user is deleted
        """
        self.inactive_user.is_active = True
        self.inactive_user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.inactive_user.save()

        # Setup files for user to be deleted
        search_criteria = self._set_up_test_search_criteria()
        original_gene_count = Gene.objects.filter(name="TRPC1").count()
        self.assertEqual(original_gene_count, 1)

        # Run the search, by posting filter and gene selection form
        self._login_user()

        path = reverse('filter_selector', kwargs={'pk': search_criteria.id})

        # Verify expected content is on the gene and filter form page
        expected_text = ["Enter genes", "Filter", "e.g. Humans"]
        self._find_expected_content(path=path, msg_list=expected_text)

        # Filter by a genes
        response = self.client.post(path, {'genes': 'TRPC1,HTR1A'}, follow=True)

        # Retrieve results object
        search_result = SearchResult.objects.get(criteria=search_criteria)

        test_results_edge_csv = open(os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_edge.csv'),
                                     'r')
        test_results_abstract_csv = open(
            os.path.join(settings.RESULTS_PATH, search_result.filename_stub + '_abstracts.csv'), 'r')
        edge_file_lines = test_results_edge_csv.readlines()
        abstract_file_lines = test_results_abstract_csv.readlines()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[1].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 9)  # Expected 9 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        search_result = SearchResult.objects.all()[0]
        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id

        upload_record = Upload.objects.get(pk=upload_id)

        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        base_path = settings.MEDIA_ROOT + '/results/' + search_result.filename_stub + '*'

        # Now make user in line for deletion
        self.user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=366)
        self.user.save()

        user_clean_up()

        # Test that no message sent
        self.assertEqual(len(mail.outbox), 0)

        # Check user deleted
        self.assertEqual((self.total_users - 1), User.objects.all().count())

        # Check records have gone
        self.assertFalse(SearchResult.objects.filter(pk=search_result_id).exists())
        self.assertFalse(SearchCriteria.objects.filter(pk=search_criteria_id).exists())
        self.assertFalse(Upload.objects.filter(pk=upload_id).exists())

        # Check files...
        self.assertFalse(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)

    def test_inactive_user_delete(self):
        """
        Test that user is deleted
        """
        self.user.last_login = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.user.save()

        user_clean_up()

        # Test that no message is sent
        self.assertEqual(len(mail.outbox), 0)

        # Check user deleted
        self.assertEqual((self.total_users - 1), User.objects.all().count())

