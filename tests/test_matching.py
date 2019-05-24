# -*- coding: utf-8 -*-
""" TeMMPo unit test suite for matching code
"""

import logging
import numpy as np
import os

from django.conf import settings
from django.test import tag

from browser.matching import create_edge_matrix, generate_synonyms # read_citations, countedges, createresultfile, printedges, createjson
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from tests.base_test_case import BaseTestCase

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(__file__)

# Valid file uploads
TEST_FILE = os.path.join(BASE_DIR, 'test-abstract.txt')
TEST_YEAR = 2018


@tag('matching-test')
class MatchingTestCase(BaseTestCase):
    """Run tests for browsing the TeMMPo application."""

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def test_create_edge_matrix(self):
        number_genes = 5
        number_of_mediators = 10
        number_of_exposures = 2
        number_of_outcomes = 4
        edges, identifiers = create_edge_matrix(number_genes, number_of_mediators, number_of_exposures, number_of_outcomes)
        self.assertTrue(type(edges), np.ndarray)
        self.assertEqual(edges.shape, (15, 6))
        self.assertEqual(np.sum(edges), 0)

        # identifier not in use at this time, so should be an empty dictionary
        self.assertTrue(type(identifiers), type({}))
        self.assertEqual(identifiers, {})

    def test_createsynonym(self):
        """TODO BUG FIX TMMA-307 - Test data structures used for gene synonym matching have been created as expected.

            wc -l Homo_sapiens.gene_info == 43855 
            gene    synonyms
            A1BG :  A1B|ABG|GAB|HYST2477
            CCAT2   LINC00873|NCCP1
        """
        synonymlookup, synonymlisting = generate_synonyms()

        self.assertTrue(type(synonymlookup), type({}))
        self.assertTrue(type(synonymlisting), type({}))
        self.assertTrue(len(synonymlisting), 43855)

        # Find the gene name itself when checking for it's synonym
        self.assertEqual(synonymlookup["A1BG"], "A1BG")
        self.assertEqual(synonymlookup["CCAT2"], "CCAT2")

        # Ensure all the expected synomyns have been recorded
        # self.assertEqual(synonymlookup["A1B"], "A1BG")
        # TODO TMMA-307 Confirm with Tom how to handle this lack of ability for a direct lookup should a synonym. be matched against all it's alias gene names?
        self.assertEqual(synonymlookup["ABG"], "A1BG")
        self.assertEqual(synonymlookup["GAB"], "A1BG")
        # self.assertEqual(synonymlookup["GAB"], "HYST2477")
        # TODO TMMA-307

        self.assertEqual(synonymlookup["LINC00873"], "CCAT2")
        self.assertEqual(synonymlookup["NCCP1"], "CCAT2")

        self.assertEqual(synonymlisting["A1BG"], ["A1B","ABG","GAB","HYST2477","A1BG",])
        self.assertEqual(synonymlisting["CCAT2"], ["LINC00873","NCCP1","CCAT2",])

    # def test_createedgelist(self):
    #     assert False

    # def read_citations(self):
    #     assert False

    # def test_countedges(self):
    #     assert False

    # def test_createresultfile(self):
    #     assert False

    # def test_printedges(self):
    #     assert False

    # def test_createjson(self):
    #     assert False