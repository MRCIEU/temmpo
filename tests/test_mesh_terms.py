# -*- coding: utf-8 -*-
""" Test Mesh Term year filter helper functions
"""
from collections import OrderedDict
import logging

from django.core.urlresolvers import reverse
from django.test import TestCase

from browser.models import MeshTerm
from browser.views import (_get_latest_mesh_term_release_year, 
    _get_top_level_mesh_terms, 
    _get_mesh_terms_by_year, 
    _convert_terms_to_current_year, )


class TestMeshTermsReleaseYears(TestCase):

    def _set_up_tree(self, terms, year):
        for (term, parent_term) in terms.items():
            parent = None
            if parent_term:
                parent = MeshTerm.objects.get(term=parent_term, year=year)
            MeshTerm.objects.create(term=term, parent=parent, year=year, tree_number="N/A")

    def setUp(self):
        super(TestMeshTermsReleaseYears, self).setUp()
        self.year_2015_terms = OrderedDict([('2015', None,),
            ('A', '2015',),
            ('AA', 'A',),
            ('B', '2015',),
            ('C', '2015',),])
        self.year_2018_terms = OrderedDict([('2018', None,),
            ('A', '2018',),
            ('B', '2018',),
            ('C', '2018',),
            ('CC', 'C',),
            ('D', '2018',),])
        self._set_up_tree(self.year_2015_terms, 2015)
        self._set_up_tree(self.year_2018_terms, 2018)
        self.latest_release = 2018

    def test_get_latest_mesh_term_release_year(self):
        # Based on current test terms
        self.assertEqual(self.latest_release, _get_latest_mesh_term_release_year())
        # Ensure new years are also taken into account.
        new_year = 2019
        new_year_tree = OrderedDict([(str(new_year), None,),
                                ('A', str(new_year),), ])
        self._set_up_tree(new_year_tree, new_year)
        self.assertEqual(new_year, _get_latest_mesh_term_release_year())

    def test_get_top_level_mesh_terms(self):
        expected_terms_2015 = ['A', 'B', 'C',]
        expected_terms_2018 = ['A', 'B', 'C', 'D',]
        found_terms_2015 = [x.term for x in _get_top_level_mesh_terms(2015)]
        found_terms_2018 = [x.term for x in _get_top_level_mesh_terms(2018)]
        self.assertEqual(expected_terms_2015, found_terms_2015)
        self.assertEqual(expected_terms_2018, found_terms_2018)

    def test_get_mesh_terms_by_year(self):
        expected_terms_2015 = ['A', 'AA', 'B', 'C',]
        expected_terms_2018 = ['A', 'B', 'C', 'CC', 'D',]
        found_terms_2015 = [x.term for x in _get_mesh_terms_by_year(2015)]
        found_terms_2018 = [x.term for x in _get_mesh_terms_by_year(2018)]
        found_terms_current_year = [x.term for x in _get_mesh_terms_by_year()]
        self.assertEqual(found_terms_2015, expected_terms_2015)
        self.assertEqual(found_terms_2018, expected_terms_2018)
        self.assertEqual(found_terms_current_year, expected_terms_2018)

    def test_convert_terms_to_current_year(self):        
        terms_for_2015 = MeshTerm.objects.filter(term__in=['A', 'AA', 'B', 'C',], year=2015)
        expected_in_2018_terms = [x.term for x in MeshTerm.objects.filter(term__in=['A', 'B', 'C',], year=2018)]
        converted_terms_names = [x.term for x in _convert_terms_to_current_year(terms_for_2015, 2015, 2018)]
        self.assertEqual(expected_in_2018_terms, converted_terms_names)

    def test_convert_terms_to_current_year_non_found(self):
        terms_only_in_2015 = MeshTerm.objects.filter(term__in=['AA'])
        result = _convert_terms_to_current_year(terms_only_in_2015, 2015, 2018)
        self.assertEqual(len(result), 0)        
