# -*- coding: utf-8 -*-
""" TeMMPo unit test suite for matching code
"""

import logging
import numpy as np
import os
import shutil

from django.conf import settings
from django.core.files import File
from django.test import tag

from browser.matching import create_edge_matrix, generate_synonyms # ,read_citations, countedges, printedges, createjson
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from browser.matching import record_differences_between_match_runs, perform_search
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

    def _prepare_search_result(self):
        """Generates a search result object and associated edge file

        Mediators,Exposure counts,Outcome counts,Scores
        Genetic Markers,2,1,1.5
        Genetic Pleiotropy,1,1,2.0
        Serogroup,2,1,1.5
        """
        year = 2018
        BASE_DIR = os.path.dirname(__file__)
        test_file_path = os.path.join(BASE_DIR, 'test-abstract-ovid-test-sample-5.txt')

        test_file = open(test_file_path, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract-ovid-test-sample-5.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        exposure_term = MeshTerm.objects.get(term="Cells", year=year).get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Public Health Systems Research", year=year).get_descendants(include_self=True)
        # gene = Gene.objects.get(name="TRPC1") # Extend gene testing to include STIM1 or a synonym or two

        search_criteria = SearchCriteria(upload=upload, mesh_terms_year_of_release=year)
        search_criteria.save()

        # search_criteria.genes.add(gene)
        search_criteria.exposure_terms = exposure_term
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()

        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        # Run the search via message queue
        perform_search(search_result.id)

        return search_result.id

        # Copy and amend edge results files for testing

    def test_record_differences_between_match_runs_no_previous_search(self):
        """No version 1 search results"""
        search_result_id = self._prepare_search_result()
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertEqual(search_result.mediator_match_counts, None)
        self.assertFalse(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertFalse(search_result.has_edge_file_changed)

        record_differences_between_match_runs(search_result_id)

        search_result = SearchResult.objects.get(id=search_result_id)
        self.assertEqual(search_result.mediator_match_counts, None)
        self.assertFalse(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertFalse(search_result.has_edge_file_changed)

    def test_record_differences_between_match_runs_missing_v1_edge_file(self):
        """Previous search results but missing edge file"""
        search_result_id = self._prepare_search_result()
        search_result = SearchResult.objects.get(id=search_result_id)
        search_result.mediator_match_counts = 0
        search_result.save()

        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)

        try:
            record_differences_between_match_runs(search_result_id)
            # Expected to throw an exception and not reach the next line
            assert False
        except IOError:
            assert True
            search_result = SearchResult.objects.get(id=search_result_id)
            self.assertTrue(search_result.has_changed)
            self.assertTrue(search_result.has_match_counts_changed)
        except:
            raise

    def test_record_differences_between_match_runs_missing_v3_edge_file(self):
        """Previous search results but missing edge file"""
        search_result_id = self._prepare_search_result()
        search_result = SearchResult.objects.get(id=search_result_id)
        search_result.mediator_match_counts = 0
        search_result.save()
        shutil.move(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv", settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv")

        try:
            record_differences_between_match_runs(search_result_id)
            # Expected to throw an exception and not reach the next line
            assert False
        except IOError:
            assert True
            search_result = SearchResult.objects.get(id=search_result_id)
            self.assertTrue(search_result.has_changed)
            self.assertTrue(search_result.has_match_counts_changed)
        except:
            raise

    def test_record_differences_between_match_runs_no_changes_expected(self):
        """Previous search, edge file and no changes expected"""
        search_result_id = self._prepare_search_result()
        search_result = SearchResult.objects.get(id=search_result_id)
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3
        search_result.save()
        shutil.copyfile(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv", settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertFalse(search_result.has_changed)
        self.assertFalse(search_result.has_edge_file_changed)


    def test_record_differences_between_match_runs_when_changes_exist(self):
        """Previous search, edge file and change in counts and scores expected in line 1, n/2, and n"""
        search_result_id = self._prepare_search_result()
        search_result = SearchResult.objects.get(id=search_result_id)
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3
        search_result.save()

        #Amend line 1 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,1,1,1\n")
            file.write("Genetic Pleiotropy,1,1,2.0\n")
            file.write("Serogroup,2,1,1.5\n")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Amend line n/2 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5\n")
            file.write("Genetic Pleiotropy,2,1,1.5\n")
            file.write("Serogroup,2,1,1.5\n")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Amend last line found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5\n")
            file.write("Genetic Pleiotropy,1,1,2.0\n")
            file.write("Serogroup,1,1,1\n")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)


    def test_record_differences_between_match_runs_when_new_meditors(self):
        """Previous search, edge file and new mediators expected in line 1, n/2, and n"""
        search_result_id = self._prepare_search_result()
        search_result = SearchResult.objects.get(id=search_result_id)
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3 - 1
        search_result.save()

        #Remove line 1 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Pleiotropy,1,1,2.0\n")
            file.write("Serogroup,2,1,1.5\n")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertNotEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Remove line n/2 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5\n")
            file.write("Serogroup,2,1,1.5\n")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertNotEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Remove last line found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5\n")
            file.write("Genetic Pleiotropy,1,1,2.0\n")

        record_differences_between_match_runs(search_result_id)
        search_result = SearchResult.objects.get(id=search_result_id)

        self.assertNotEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)
