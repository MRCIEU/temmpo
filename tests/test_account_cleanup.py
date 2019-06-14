# -*- coding: utf-8 -*-
"""Test non mesh term functionality."""
from datetime import datetime, timedelta
import glob
import os
import shutil

from django.utils import timezone
from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.test import tag

from tests.base_test_case import BaseTestCase
from browser.matching import perform_search
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from browser.utils import user_clean_up, delete_user_content


BASE_DIR = os.path.dirname(__file__)
TEST_FILE = os.path.join(BASE_DIR, 'test-abstract.txt')
TEST_YEAR = 2018

@tag('cleanup-test')
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
        test_results_edge_csv.close()
        test_results_abstract_csv.close()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[2].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 8)  # Expected 8 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        # Go to results page
        response = self.client.get(reverse('results_listing'))

        # Check delete button
        self.assertContains(response, 'delete-label', count=1)
        self.assertContains(response, 'delete-button', count=1)

        search_result = SearchResult.objects.all()[0]
        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id

        # Check files...
        # Check abstract
        upload_record = Upload.objects.get(pk=upload_id)

        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 3)

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
        test_results_edge_csv.close()
        test_results_abstract_csv.close()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[2].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 8)  # Expected 8 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        self.assertContains(response, "Search criteria for resultset '%s'" % search_result.id)

        # Go to results page
        response = self.client.get(reverse('results_listing'))

        # Check delete button
        self.assertContains(response, 'delete-label', count=1)
        self.assertContains(response, 'delete-button', count=1)

        search_result = SearchResult.objects.all()[0]
        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id

        # Check files...
        # Check abstract
        upload_record = Upload.objects.get(pk=upload_id)

        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        # Check results files
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 3)

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


    def test_delete_user_content_unsubmitted_search_criteria(self):
        """Ensure that saved search criteria which has not been submitted for a search is also deleted."""
        search_criteria = self._set_up_test_search_criteria()
        upload = search_criteria.upload

        # Ensure no related search result exists
        self.assertFalse(SearchResult.objects.filter(criteria=search_criteria).exists())

        delete_user_content(search_criteria.upload.user.id)

        # Ensure stub search criteria has been removed.
        self.assertFalse(SearchCriteria.objects.filter(id=search_criteria.id).exists())

        # Ensure file upload has been removed.
        self.assertFalse(Upload.objects.filter(id=upload.id).exists())

    def test_delete_user_content_where_upload_was_reused(self):
        search_criteria = self._set_up_test_search_criteria()
        upload = search_criteria.upload
        user_id = search_criteria.upload.user.id
        additional_search_criteria = self._set_up_test_search_criteria()
        additional_search_criteria.upload = upload
        additional_search_criteria.save()

        delete_user_content(user_id)

        # Ensure search criteria has been removed.
        self.assertFalse(SearchCriteria.objects.filter(id=search_criteria.id).exists())
        self.assertFalse(SearchCriteria.objects.filter(id=additional_search_criteria.id).exists())

        # Ensure file upload has been removed.
        self.assertFalse(Upload.objects.filter(id=upload.id).exists())

    def test_upload_delete_with_no_search_result(self):
        search_criteria = self._set_up_test_search_criteria()
        upload = search_criteria.upload

        upload.delete()

        # Ensure file upload has been removed.
        self.assertFalse(Upload.objects.filter(id=upload.id).exists())

    def test_delete_search_result_that_has_not_began_processing(self):
        """Test to ensure this bug does not appear again TMMA-260."""
        search_criteria = self._set_up_test_search_criteria()
        upload = search_criteria.upload

        # Prepare the stub search result object but do not start processing the search
        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        delete_user_content(search_criteria.upload.user.id)

        # Ensure search criteria has been removed.
        self.assertFalse(SearchCriteria.objects.filter(id=search_criteria.id).exists())

        # Ensure file upload has been removed.
        self.assertFalse(Upload.objects.filter(id=upload.id).exists())

        # Ensure stub search result has been removed.
        self.assertFalse(SearchResult.objects.filter(id=search_result.id).exists())


@tag('cleanup-test')
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
        test_results_edge_csv.close()
        test_results_abstract_csv.close()
        self.assertEqual(len(edge_file_lines), 3)  # Expected two matches and a line of column headings
        self.assertEqual(edge_file_lines[0].strip(), "Mediators,Exposure counts,Outcome counts,Scores")
        self.assertEqual(edge_file_lines[2].strip(), "Phenotype,4,1,1.25")
        self.assertEqual(len(abstract_file_lines), 8)  # Expected 8 lines including header
        self.assertEqual(abstract_file_lines[0].strip(), "Abstract IDs")
        self.assertEqual(abstract_file_lines[1].strip(), "23266572")
        self.assertTrue(search_result.has_completed)
        search_result = SearchResult.objects.all()[0]
        search_result_id = search_result.id
        search_criteria_id = search_result.criteria.id
        upload_id = search_result.criteria.upload.id

        upload_record = Upload.objects.get(pk=upload_id)

        self.assertTrue(os.path.exists(upload_record.abstracts_upload.file.name))
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'

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


    def test_delete_user_content_version_1_matching(self):
        """Ensure version 1 files are also deleted"""
        search_criteria = self._set_up_test_search_criteria()
        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        # Run the search via message queue
        perform_search(search_result.id)

        # Retrieve results object
        search_result = SearchResult.objects.get(id=search_result.id)

        # Check v3 matching results files
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 3)

        # Mock up some v1 results files
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3 
        search_result.save()
        shutil.copyfile(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv", settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv")
        shutil.copyfile(settings.RESULTS_PATH + search_result.filename_stub + "_abstracts.csv", settings.RESULTS_PATH_V1 + search_result.filename_stub + "_abstracts.csv")
        shutil.copyfile(settings.RESULTS_PATH + search_result.filename_stub + ".json", settings.RESULTS_PATH_V1 + search_result.filename_stub + ".json")

        # Check v1 matching results files
        base_path = settings.RESULTS_PATH_V1 + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 3)

        delete_user_content(search_criteria.upload.user.id)

        # Check v1 matching results files
        base_path = settings.RESULTS_PATH_V1 + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)

        # Check v3 matching results files
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)


    def test_delete_user_content_version_1_matching_no_hits(self):
        """Ensure version 1 files are also deleted"""
        search_criteria = self._set_up_test_search_criteria()
        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        # Run the search via message queue
        perform_search(search_result.id)

        # Retrieve results object
        search_result = SearchResult.objects.get(id=search_result.id)

        # Check v3 matching results files are created.
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 3)

        # Mock up some v1 stub results files where mediator matches were 0
        search_result.mediator_match_counts = 0 
        search_result.save()
        file_stub = open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w")
        file_stub.write("Mediators,Exposure counts,Outcome counts,Scores\n")
        file_stub = open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_abstracts.csv", "w")
        file_stub.write("Abstract IDs\n")
        file_stub.close()
        file_stub = open(settings.RESULTS_PATH_V1 + search_result.filename_stub + ".json", "w")
        file_stub.close()

        # Check v1 matching results files exist
        base_path = settings.RESULTS_PATH_V1 + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 3)

        delete_user_content(search_criteria.upload.user.id)

        # Check v1 matching results files are deleted.
        base_path = settings.RESULTS_PATH_V1 + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)

        # Check v3 matching results files are deleted.
        base_path = settings.RESULTS_PATH + search_result.filename_stub + '*'
        files_to_delete = glob.glob(base_path)
        self.assertEqual(len(files_to_delete), 0)