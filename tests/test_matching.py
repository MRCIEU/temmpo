# -*- coding: utf-8 -*-
""" TeMMPo unit test suite for matching code
"""

import logging
import numpy as np
import os

from django.conf import settings
from django.test import tag

from browser.matching import create_edge_matrix, generate_synonyms # ,read_citations, countedges, createresultfile, printedges, createjson
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from tests.base_test_case import BaseTestCase

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(__file__)
TEST_FILE = os.path.join(BASE_DIR, 'test-abstract.txt')
TEST_YEAR = 2018

@tag('matching-test')
class MatchingTestCase(BaseTestCase):
    """Run tests for performing matches in the TeMMPo application."""

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
        """Test data structures used for gene synonym matching have been created as expected.

            wc -l Homo_sapiens.gene_info == 43855 
            gene    synonyms
            A1BG :  A1B|ABG|GAB|HYST2477
            CCAT2   LINC00873|NCCP1
        """
        synonymlookup, synonymlisting = generate_synonyms()

        # Find the gene name itself when checking for it's synonym
        self.assertEqual(synonymlookup["A1BG"][0], "A1BG")
        self.assertEqual(len(synonymlookup["A1BG"]), 1)  # Is a gene name not a synonym.
        self.assertEqual(synonymlookup["CCAT2"][0], "CCAT2")
        self.assertEqual(len(synonymlookup["CCAT2"]), 1)  # Is a gene name not a synonym.

        # Ensure all the expected synonyms have been recorded
        self.assertEqual(synonymlookup["A1B"][0], "A1BG")
        self.assertEqual(synonymlookup["A1B"][1], "SNTB1")
        self.assertEqual(len(synonymlookup["A1B"]), 2)  # TMMA-307: Testing a synonym that is used for two different genes.
        self.assertEqual(synonymlookup["ABG"][0], "A1BG")
        self.assertEqual(len(synonymlookup["ABG"]), 1) # Is a synonym that is used for 1 gene
        self.assertEqual(synonymlookup["GAB"][0], "A1BG")
        self.assertEqual(synonymlookup["HYST2477"][0], "A1BG")

        self.assertEqual(synonymlookup["LINC00873"][0], "CCAT2")
        self.assertEqual(synonymlookup["NCCP1"][0], "CCAT2")

        self.assertEqual(synonymlisting["A1BG"], ["A1B","ABG","GAB","HYST2477","A1BG",])
        self.assertEqual(synonymlisting["CCAT2"], ["LINC00873","NCCP1","CCAT2",])

    def test_synonym_listing_looks_ups(self):
        header_rows = 1
        known_double_gene_entries = ("16S",) # The last line is in there twice for this version of Homo_sapiens.gene_info
        synonymlookup, synonymlisting = generate_synonyms()
        self.assertTrue(type(synonymlookup), type({}))
        self.assertTrue(type(synonymlisting), type({}))
        self.assertTrue(len(synonymlisting), 43855 - header_rows + len(known_double_gene_entries))

    def test_last_line_of_gene_synonym_file_is_processed(self):
        synonymlookup, synonymlisting = generate_synonyms()
        self.assertEqual(synonymlookup["16S"][0], "16S")
        self.assertEqual(len(synonymlookup["16S"]), 1)
        self.assertEqual(synonymlisting["16S"], ["16S",])

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