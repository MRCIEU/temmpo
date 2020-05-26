# -*- coding: utf-8 -*-
"""Test view authorisation"""
import os

from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import tag

from browser.matching import perform_search
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, Gene
from tests.base_test_case import BaseTestCase

@tag('admin')
class AdminTestCase(BaseTestCase):
    """Run simple tests for basic admin pages customisations in TeMMPo application."""

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def _create_upload_object(self):
        """Create and return a test upload object."""
        BASE_DIR = os.path.dirname(__file__)
        test_file_path = os.path.join(BASE_DIR, 'test-abstract-ovid-test-sample-5.txt')

        test_file = open(test_file_path, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract-ovid-test-sample-5.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        return upload

    def _create_search_criteria(self):
        """Create and return a test search criteria object."""
        year = 2018
        exposure_term = MeshTerm.objects.get(term="Cells", year=year).get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Public Health Systems Research", year=year).get_descendants(include_self=True)
        gene = Gene.objects.get(name="TRPC1")

        search_criteria = SearchCriteria(upload=self._create_upload_object(), mesh_terms_year_of_release=year)
        search_criteria.save()

        search_criteria.genes.add(gene)
        search_criteria.exposure_terms = exposure_term
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()

        return search_criteria

    def _create_search_result(self):
        """Create and return a stub test search result object"""
        search_result = SearchResult(criteria=self._create_search_criteria())
        search_result.save()
        return search_result

    def test_mesh_terms_admin_list(self):
        """Test super user accessing mesh term listing admin pages"""
        self.client.logout()
        self._login_super_user()
        expected_form = ["Select mesh term to change", "Search", "Add mesh term"]
        self._find_expected_content('/admin/browser/meshterm', msg_list=expected_form)

    def test_mesh_terms_admin_edit(self):
        """Test super user accessing mesh term edit admin pages"""
        path = '/admin/browser/meshterm/16493/change/'
        self.client.logout()
        self._login_super_user()
        expected_form = ["2015", "Parent", "Tree number", "Year", "Term", ]
        self._find_expected_content(path, msg_list=expected_form)
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'class="readonly"', count=4)

    def test_genes_admin_list(self):
        """Test super user accessing gene listing admin pages"""
        self.client.logout()
        self._login_super_user()
        expected_form = ["Select gene to change", "Search", "Add gene"]
        self._find_expected_content('/admin/browser/gene', msg_list=expected_form)

    def test_genes_admin_edit(self):
        """Test super user accessing gene edit admin pages"""
        path = '/admin/browser/gene/21899/change/'
        self.client.logout()
        self._login_super_user()
        expected_form = ["TRPC1", "Synonym for:"]
        self._find_expected_content(path, msg_list=expected_form)
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'class="readonly"', count=2)

    def test_messages_admin_list(self):
        """Test super user accessing gene listing admin pages"""
        self.client.logout()
        self._login_super_user()
        expected_form = ["Select message to change", "Add message"]
        self._find_expected_content('/admin/browser/message', msg_list=expected_form)

    def test_messages_admin_edit(self):
        """Test super user accessing gene edit admin pages"""
        path = '/admin/browser/gene/21899/change/'
        self.client.logout()
        self._login_super_user()
        expected_form = ["TRPC1", "Synonym for:"]
        self._find_expected_content(path, msg_list=expected_form)
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'class="readonly"', count=2)

    def test_upload_admin_list(self):
        """Test super user accessing upload listing admin pages"""
        self.client.logout()
        self._login_super_user()
        expected_form = ["Select upload to change", "Add upload"]
        self._find_expected_content('/admin/browser/upload', msg_list=expected_form)

    def test_upload_admin_edit(self):
        """Test super user accessing upload edit admin pages"""
        self.client.logout()
        self._login_super_user()
        # Create a test upload object
        upload = self._create_upload_object()
        path = '/admin/browser/upload/%d/change/' % upload.id
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'class="readonly"', count=3)
        self.assertContains(response, 'test-abstract-ovid-test-sample-5.txt')

    def test_search_criteria_admin_list(self):
        """Test super user accessing search criteria listing admin pages"""
        self.client.logout()
        self._login_super_user()
        expected_form = ["Select search criteria to change", "Add search criteria"]
        self._find_expected_content('/admin/browser/searchcriteria', msg_list=expected_form)

    def test_search_criteria_admin_edit(self):
        """Test super user accessing search criteria admin pages"""
        # Create test search criteria object
        search_criteria = self._create_search_criteria()
        path = '/admin/browser/searchcriteria/%d/change/' % search_criteria.id
        self.client.logout()
        self._login_super_user()
        expected_form = ["Phenotype", "TRPC1", "Public Health Systems Research", "Cells", ]
        self._find_expected_content(path, msg_list=expected_form)
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'class="readonly"', count=7)

    def test_search_result_admin_list(self):
        """Test super user accessing search result listing admin pages"""
        self.client.logout()
        self._login_super_user()
        # Check listing with a stub search result object
        search_result = self._create_search_result()
        expected_form = ["Select search result to change", "Add search result", "SearchResult id:", "Not started"]
        self._find_expected_content('/admin/browser/searchresult', msg_list=expected_form)
        # Check listing matching has been performed
        perform_search(search_result.id)
        # Retrieve the updated search results object
        search_result = SearchResult.objects.get(id=search_result.id)
        expected_form = [search_result.filename_stub, "Completed"]
        self._find_expected_content('/admin/browser/searchresult', msg_list=expected_form)

    def test_search_result_edit_list(self):
        """Test super user accessing search result admin pages"""
        # Create test search result object
        search_result = self._create_search_result()
        path = '/admin/browser/searchresult/%d/change/' % search_result.id
        self.client.logout()
        self._login_super_user()
        # Check form with a stub search result object
        expected_form = ["Filename stub", "Has edge file changed", "Criteria", ]
        self._find_expected_content(path, msg_list=expected_form)
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'class="readonly"', count=9)
        # Check form after a matching has been performed
        perform_search(search_result.id)
        # Retrieve the updated search results object
        search_result = SearchResult.objects.get(id=search_result.id)
        expected_form = ["results_%d__topresults" % search_result.id, ]
        self._find_expected_content(path, msg_list=expected_form)