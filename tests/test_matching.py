# -*- coding: utf-8 -*-
""" TeMMPo unit test suite for matching code
"""
import csv
import io
import json
import logging
import os
import shutil

from csvvalidator import *
import numpy as np
import pandas as pd

from django.conf import settings
from django.core.files import File
from django.core import management
from django.core.urlresolvers import reverse
from django.test import tag

from browser.matching import Citation, create_edge_matrix, generate_synonyms, read_citations, countedges, printedges, createjson, _get_genes_and_mediators
from browser.matching import record_differences_between_match_runs, perform_search, pubmed_matching_function, ovid_matching_function, searchgene
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from tests.base_test_case import BaseTestCase

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(__file__)


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

    def test_read_citations_ovid(self):
        citations = read_citations(file_path=BASE_DIR + "/test-abstract-ovid-test-sample-5.txt", file_format=OVID)

        # Check for expected structure
        expected_fields = ("Unique Identifier", "MeSH Subject Headings", "Abstract", )
        citation_count = 0
        for citation in citations:
            citation_count +=1
            for field in expected_fields:
                self.assertTrue(citation.fields.has_key(field))
            if citation_count == 2:
                # Spot check for expected contents
                self.assertEqual("999992", citation.fields["Unique Identifier"].strip())
                self.assertTrue("Pyroptosis" in citation.fields["MeSH Subject Headings"])
                self.assertTrue("pulvinar placerat exexex" in citation.fields["Abstract"])

        self.assertEqual(citation_count, 5)

    def test_read_citations_pubmed(self):
        citations = read_citations(file_path=BASE_DIR + "/pubmed_result_100.txt", file_format=PUBMED)
        citation_count = 0
        expected_field = "PMID"
        for citation in citations:
            citation_count +=1
            self.assertTrue(citation.fields.has_key(expected_field))
            if citation.fields["PMID"] == "26124321":
                self.assertTrue("Cell Line, Tumor" in citation.fields["MH"])
                self.assertTrue("transfected with CYP27B" in citation.fields["AB"])
        self.assertEqual(citation_count, 100)

    def _prepare_base_search_criteria(self, year, file_name=u'test-abstract-ovid-test-sample-5.txt', file_format=OVID):
        BASE_DIR = os.path.dirname(__file__)
        test_file_path = os.path.join(BASE_DIR, file_name)
        test_file = open(test_file_path, 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, file_name), file_format=OVID)
        upload.save()
        test_file.close()

        search_criteria = SearchCriteria(upload=upload, mesh_terms_year_of_release=year)
        search_criteria.save()
        return search_criteria

    def _prepare_search_result(self, file_name=u'test-abstract-ovid-test-sample-5.txt', file_format=OVID):
        """Generates a search result object and associated edge file

        Mediators,Exposure counts,Outcome counts,Scores
        Genetic Markers,2,1,1.5
        Genetic Pleiotropy,1,1,2.0
        Serogroup,2,1,1.5
        """
        year = 2018
        search_criteria = self._prepare_base_search_criteria(year, file_name, file_format)

        exposure_term = MeshTerm.objects.get(term="Cells", year=year).get_descendants(include_self=True)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Public Health Systems Research", year=year).get_descendants(include_self=True)
        # gene = Gene.objects.get(name="TRPC1") # Extend gene testing to include STIM1 or a synonym or two

        # search_criteria.genes.add(gene)
        search_criteria.exposure_terms = exposure_term
        search_criteria.outcome_terms = outcome_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.save()

        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        perform_search(search_result.id)

        return SearchResult.objects.get(id=search_result.id)


    def test_record_differences_between_match_runs_no_previous_search(self):
        """No version 1 search results"""
        search_result = self._prepare_search_result()

        self.assertEqual(search_result.mediator_match_counts, None)
        self.assertFalse(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertFalse(search_result.has_edge_file_changed)

        record_differences_between_match_runs(search_result.id)

        search_result = SearchResult.objects.get(id=search_result.id)
        self.assertEqual(search_result.mediator_match_counts, None)
        self.assertFalse(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertFalse(search_result.has_edge_file_changed)

    def test_record_differences_between_match_runs_missing_v1_edge_file(self):
        """Previous search results but missing edge file"""
        search_result = self._prepare_search_result()
        search_result.mediator_match_counts = 0
        search_result.save()

        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)

        try:
            record_differences_between_match_runs(search_result.id)
            # Expected to throw an exception and not reach the next line
            logger.error("Expected version 1 edge file %s_edge.csv to be missing and an exception to be thrown." % search_result.filename_stub)
            assert False
        except IOError:
            assert True
            search_result = SearchResult.objects.get(id=search_result.id)
            self.assertTrue(search_result.has_changed)
            self.assertTrue(search_result.has_match_counts_changed)
        except:
            raise

    def test_record_differences_between_match_runs_missing_v3_edge_file(self):
        """Previous search results but missing edge file"""
        search_result = self._prepare_search_result()
        search_result.mediator_match_counts = 0
        search_result.save()
        shutil.move(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv", settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv")

        try:
            record_differences_between_match_runs(search_result.id)
            # Expected to throw an exception and not reach the next line
            assert False
        except IOError:
            assert True
            search_result = SearchResult.objects.get(id=search_result.id)
            self.assertTrue(search_result.has_changed)
            self.assertTrue(search_result.has_match_counts_changed)
        except:
            raise

    def test_record_differences_between_match_runs_no_changes_expected(self):
        """Previous search, edge file and no changes expected"""
        search_result = self._prepare_search_result()
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3
        search_result.save()
        # Add trailing commas to the V1 file no longer present in v3 files
        with open(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv", "r") as v3_csv:
            data = v3_csv.readlines()
            for i in range(1, len(data)):
                data[i] = data[i].strip() + ",\n"
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as v1_csv:
            v1_csv.writelines(data)

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertFalse(search_result.has_changed)
        self.assertFalse(search_result.has_edge_file_changed)


    def test_record_differences_between_match_runs_when_changes_exist(self):
        """Previous search, edge file and change in counts and scores expected in line 1, n/2, and n"""
        search_result = self._prepare_search_result()
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3
        search_result.save()

        #Amend line 1 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,1,1,1,\n")
            file.write("Genetic Pleiotropy,1,1,2.0,\n")
            file.write("Serogroup,2,1,1.5,\n")

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Amend line n/2 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5,\n")
            file.write("Genetic Pleiotropy,2,1,1.5,\n")
            file.write("Serogroup,2,1,1.5,\n")

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Amend last line found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5,\n")
            file.write("Genetic Pleiotropy,1,1,2.0,\n")
            file.write("Serogroup,1,1,1,\n")

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertFalse(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)


    def test_record_differences_between_match_runs_when_new_meditors(self):
        """Previous search, edge file and new mediators expected in line 1, n/2, and n"""
        search_result = self._prepare_search_result()
        search_result.mediator_match_counts = search_result.mediator_match_counts_v3 - 1
        search_result.save()

        #Remove line 1 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Pleiotropy,1,1,2.0,\n")
            file.write("Serogroup,2,1,1.5,\n")

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertNotEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Remove line n/2 found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5,\n")
            file.write("Serogroup,2,1,1.5,\n")

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertNotEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

        # Remove last line found in the v1 results file
        with open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w") as file:
            file.write("Mediators,Exposure counts,Outcome counts,Scores\n")
            file.write("Genetic Markers,2,1,1.5,\n")
            file.write("Genetic Pleiotropy,1,1,2.0,\n")

        record_differences_between_match_runs(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        self.assertNotEqual(search_result.mediator_match_counts, search_result.mediator_match_counts_v3)
        self.assertTrue(search_result.has_changed)
        self.assertTrue(search_result.has_match_counts_changed)
        self.assertTrue(search_result.has_edge_file_changed)

    def _get_egde_csv_data_validation_issues(self, data):
        field_names = ('Mediators',
                       'Exposure counts',
                       'Outcome counts',
                       'Scores',
                       )
        validator = CSVValidator(field_names)
        validator.add_value_check('Exposure counts', float,
                          'EX1', 'exposure count must be a float')
        validator.add_value_check('Outcome counts', float,
                          'EX2', 'outcome count must be a float')
        validator.add_value_check('Scores', float,
                          'EX3', 'scores must be a float')
        validator.add_value_check('Mediators', str,
                          'EX4', 'mediators must be a string')
        return validator.validate(data)

    def test_serving_results_edge_csv_file(self):
        self._login_user()
        search_result = self._prepare_search_result()
        path = reverse('count_data', kwargs={'pk': search_result.id })
        file_name_stub = SearchResult.objects.get(id=search_result.id).filename_stub
        expected_url = "%s%s_edge.csv" % (settings.RESULTS_URL, file_name_stub)
        response = self.client.get(path, follow=True)
        content = response.getvalue()
        self.assertRedirects(response, expected_url, status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        # Check for expected content
        self.assertTrue("Mediators,Exposure counts,Outcome counts,Scores" in content)
        self.assertTrue("Genetic Pleiotropy,1,1,2.0" in content)
        # Validate CSV data
        csv_data = csv.reader(io.StringIO(content.decode('utf-8')))
        self.assertEqual(self._get_egde_csv_data_validation_issues(csv_data), [])

    def test_serving_v1_results_edge_csv_file(self):
        self._login_user()
        search_result = self._prepare_search_result()
        search_result.mediator_match_counts = 1
        search_result.save()
        # Create a test version 1 file
        v1_file = open(settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv", "w")
        v1_file.write("Mediators,Exposure counts,Outcome counts,Scores\nTESITNG v1 file,0,0,0,\n")
        v1_file.close()
        path = reverse('count_data_v1', kwargs={'pk': search_result.id })
        expected_url = "%s%s_edge.csv" % (settings.RESULTS_URL_V1, search_result.filename_stub)
        response = self.client.get(path, follow=True)
        content = response.getvalue()
        self.assertRedirects(response, expected_url, status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        # Check for expected content
        self.assertTrue("Mediators,Exposure counts,Outcome counts,Scores" in content)
        self.assertTrue("TESITNG v1 file,0,0,0" in content)
        # Validate CSV data
        csv_data = csv.reader(io.StringIO(content.decode('utf-8')))
        self.assertEqual(self._get_egde_csv_data_validation_issues(csv_data), [])

    def test_serving_results_json_file(self):
        self._login_user()
        search_result = self._prepare_search_result()
        path = reverse('json_data', kwargs={'pk': search_result.id })
        file_name_stub = SearchResult.objects.get(id=search_result.id).filename_stub
        expected_url = "%s%s.json" % (settings.RESULTS_URL, file_name_stub)
        response = self.client.get(path, follow=True)
        content = response.getvalue()
        self.assertRedirects(response, expected_url, status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertTrue("Genetic Pleiotropy" in content)
        # Validate contents is valid JSON
        result_json_data = json.loads(content)

    def test_serving_v1_results_json_file(self):
        self._login_user()
        search_result = self._prepare_search_result()
        file_name_stub = SearchResult.objects.get(id=search_result.id).filename_stub
        # Mock up a version 1 matching result file
        shutil.copyfile(settings.RESULTS_PATH + file_name_stub + ".json", settings.RESULTS_PATH_V1 + file_name_stub + ".json")
        path = reverse('json_data_v1', kwargs={'pk': search_result.id })
        expected_url = "%s%s.json" % (settings.RESULTS_URL_V1, file_name_stub)
        self.assertTrue("v1" in expected_url)
        response = self.client.get(path, follow=True)
        content = response.getvalue()
        self.assertRedirects(response, expected_url, status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertTrue("Genetic Pleiotropy" in content)
        # Validate contents is valid JSON
        result_json_data = json.loads(content)

    def _get_abstract_csv_data_validation_issues(self, data):
        field_names = ('Abstract IDs',)
        validator = CSVValidator(field_names)
        validator.add_value_check('Abstract IDs', int,
                          'EX1', 'Abstract IDs must be an integer')
        return validator.validate(data)

    def test_serving_results_abstract_ids_file(self):
        self._login_user()
        search_result = self._prepare_search_result()
        path = reverse('abstracts_data', kwargs={'pk': search_result.id })
        file_name_stub = SearchResult.objects.get(id=search_result.id).filename_stub
        expected_url = "%s%s_abstracts.csv" % (settings.RESULTS_URL, file_name_stub)
        response = self.client.get(path, follow=True)
        content = response.getvalue()
        self.assertRedirects(response, expected_url, status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertTrue("999991" in content)
        self.assertTrue("999992" in content)
        self.assertTrue("999993" in content)
        self.assertTrue("999995" in content)
        # Validate CSV data
        csv_data = csv.reader(io.StringIO(content.decode('utf-8')))
        self.assertEqual(self._get_abstract_csv_data_validation_issues(csv_data), [])

    def test_serving_v1_results_abstract_ids_file(self):
        self._login_user()
        search_result = self._prepare_search_result()
        path = reverse('abstracts_data_v1', kwargs={'pk': search_result.id })
        file_name_stub = SearchResult.objects.get(id=search_result.id).filename_stub
        # Mock up a version 1 matching result file
        shutil.copyfile(settings.RESULTS_PATH + file_name_stub + "_abstracts.csv", settings.RESULTS_PATH_V1 + file_name_stub + "_abstracts.csv")
        expected_url = "%s%s_abstracts.csv" % (settings.RESULTS_URL_V1, file_name_stub)
        self.assertTrue("v1" in expected_url)
        response = self.client.get(path, follow=True)
        content = response.getvalue()
        self.assertRedirects(response, expected_url, status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertTrue("999991" in content)
        self.assertTrue("999992" in content)
        self.assertTrue("999993" in content)
        self.assertTrue("999995" in content)
        # Should not have matched with any mediator terms
        self.assertFalse("999994" in content)
        # Validate CSV data
        csv_data = csv.reader(io.StringIO(content.decode('utf-8')))
        self.assertEqual(self._get_abstract_csv_data_validation_issues(csv_data), [])

    def _get_genes_list(self):
        """Mock up a generator function to return genes"""
        return ["Example Gene A", "Example Gene B", "Example Gene B2", "Example Gene C", ]

    def _get_exposure_list(self):
        return ["Cells", "Fictional MeSH Term A", "Neoplasm Metastasis", ]

    def _get_mediator_list(self):
        return ["Fictional not found MeSH Term", "Fictional MeSH Term B", ]

    def _get_outcome_list(self):
        return ["Fictional MeSH Term AA", "Fictional MeSH Term C", "Serogroup", ]

    def _get_ovid_citation_generator(self):
        citation_1 = Citation(1)
        citation_1.addfield("Unique Identifier")
        citation_1.addfieldcontent("999991")
        citation_1.addfield("MeSH Subject Headings")
        citation_1.addfieldcontent(";Cells;;Colorectal Neoplasms/ge [Genetics];;Colorectal Neoplasms/me [Metabolism];;Eryptosis;;Fictional MeSH Term AA;;Fictional MeSH Term B;;Genetic Markers;;Genetic Pleiotropy;;Histamine/me [Metabolism];;Humans;;Male;;*Metabolic Networks and Pathways/ge [Genetics];;*Metabolomics;;Neoplasm Metastasis;;Prostatic Neoplasms/ge [Genetics];;Prostatic Neoplasms/me [Metabolism];;Prostatic Neoplasms/pa [Pathology];;Public Health Systems Research;;Serogroup;;*Transcriptome;")
        citation_1.addfield("Abstract")
        citation_1.addfieldcontent("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis in turpis aliquet, cursus nisi id, mattis augue. Pellentesque vehicula at ligula vel porta. Fusce suscipit malesuada justo. Cras convallis odio nec dolor elementum facilisis. Donec vel lobortis felis, ut gravida risus. Vivamus interdum ex libero. Phasellus id pharetra tortor. Mauris euismod convallis augue, sit amet aliquet metus hendrerit ac. Duis mattis leo maximus nisi sagittis, a pulvinar turpis fringilla. Ut pellentesque ligula purus, ut iaculis metus finibus nec. Suspendisse diam felis, aliquam sed nisl at, luctus rhoncus magna. Nullam porttitor neque eget sem sagittis rhoncus. Praesent accumsan fermentum odio, ac pellentesque dui feugiat at. In metus nisl, scelerisque eget velit at, pulvinar placerat ex. Example Gene B. ")

        citation_2 = Citation(2)
        citation_2.addfield("Unique Identifier")
        citation_2.addfieldcontent("999992")
        citation_2.addfield("MeSH Subject Headings")
        citation_2.addfieldcontent(";Colorectal Neoplasms/ge [Genetics];;Colorectal Neoplasms/me [Metabolism];;Genetic Pleiotropy;;Histamine/me [Metabolism];;Humans;;Male;;*Metabolic Networks and Pathways/ge [Genetics];;*Metabolomics;;Neoplasm Metastasis;;Prostatic Neoplasms/ge [Genetics];;Prostatic Neoplasms/me [Metabolism];;Prostatic Neoplasms/pa [Pathology];;Pyroptosis;;Serogroup;;*Transcriptome;")
        citation_2.addfield("Abstract")
        citation_2.addfieldcontent("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis in turpis aliquet, cursus nisi id, mattis augue. Pellentesque vehicula at ligula vel porta. Fusce suscipit malesuada justo. Cras convallis odio nec dolor elementum facilisis. Donec vel lobortis felis, ut gravida risus. Vivamus interdum ex libero. Phasellus id pharetra tortor. Mauris euismod convallis augue, sit amet aliquet metus hendrerit ac. Duis mattis leo maximus nisi sagittis, a pulvinar turpis fringilla. Ut pellentesque ligula purus, ut iaculis metus finibus nec. Suspendisse diam felis, aliquam sed nisl at, luctus rhoncus magna. Nullam porttitor neque eget sem sagittis rhoncus. Praesent accumsan fermentum odio, ac pellentesque dui feugiat at. In metus nisl, scelerisque eget velit at, pulvinar placerat exexex.")

        citation_3 = Citation(3)
        citation_3.addfield("Unique Identifier")
        citation_3.addfieldcontent("999993")
        citation_3.addfield("MeSH Subject Headings")
        citation_3.addfieldcontent(";Colorectal Neoplasms/ge [Genetics];;Colorectal Neoplasms/me [Metabolism];;Genetic Markers;;Histamine/me [Metabolism];;Humans;;Male;;*Metabolic Networks and Pathways/ge [Genetics];;*Metabolomics;;Neoplasm Metastasis;;Prostatic Neoplasms/ge [Genetics];;Prostatic Neoplasms/me [Metabolism];;Prostatic Neoplasms/pa [Pathology];;Serogroup;;*Transcriptome;")
        citation_3.addfield("Abstract")
        citation_3.addfieldcontent("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis in turpis aliquet, cursus nisi id, mattis augue. Pellentesque vehicula at ligula vel porta. Fusce suscipit malesuada justo. Cras convallis odio nec dolor elementum facilisis. Donec vel lobortis felis, ut gravida risus. Vivamus interdum ex libero. Phasellus id pharetra tortor. Mauris euismod convallis augue, sit amet aliquet metus hendrerit ac. Duis mattis leo maximus nisi sagittis, a pulvinar turpis fringilla. Ut pellentesque ligula purus, ut iaculis metus finibus nec. Suspendisse diam felis, aliquam sed nisl at, luctus rhoncus magna. Nullam porttitor neque eget sem sagittis rhoncus. Praesent accumsan fermentum odio, ac pellentesque dui feugiat at. In metus nisl, scelerisque eget velit at, pulvinar placerat ex. ")

        citation_4 = Citation(4)
        citation_4.addfield("Unique Identifier")
        citation_4.addfieldcontent("999994")
        citation_4.addfield("MeSH Subject Headings")
        citation_4.addfieldcontent(";Fictional MeSH Term A;;Fictional MeSH Term B;;Fictional MeSH Term C;")
        citation_4.addfield("Abstract")
        citation_4.addfieldcontent("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis in turpis aliquet, cursus nisi id, mattis augue. Pellentesque vehicula at ligula vel porta. Fusce suscipit malesuada justo. Cras convallis odio nec dolor elementum facilisis. Donec vel lobortis felis, ut gravida risus. Vivamus interdum ex libero. Phasellus id pharetra tortor. Mauris euismod convallis augue, sit amet aliquet metus hendrerit ac. Duis mattis leo maximus nisi sagittis, a pulvinar turpis fringilla. Ut pellentesque ligula purus, ut iaculis metus finibus nec. Suspendisse diam felis, aliquam sed nisl at, luctus rhoncus magna. Nullam porttitor neque eget sem sagittis rhoncus. Praesent accumsan fermentum odio, ac pellentesque dui feugiat at. In metus nisl, scelerisque eget velit at, pulvinar placerat ex. Example Gene X, Example Gene B2, Example Gene A, Example Gene Sym C. ")

        citation_5 = Citation(5)
        citation_5.addfield("Unique Identifier")
        citation_5.addfieldcontent("999995")
        citation_5.addfield("MeSH Subject Headings")
        citation_5.addfieldcontent(";Colorectal Neoplasms/ge [Genetics];;Colorectal Neoplasms/me [Metabolism];;Eryptosis;;Genetic Markers;;Histamine/me [Metabolism];;Humans;;Male;;*Metabolic Networks and Pathways/ge [Genetics];;*Metabolomics;;Neoplasm Metastasis;;Penetrance;;Prostatic Neoplasms/ge [Genetics];;Prostatic Neoplasms/me [Metabolism];;Prostatic Neoplasms/pa [Pathology];;Serogroup;;*Transcriptome;")
        citation_5.addfield("Abstract")
        citation_5.addfieldcontent("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis in turpis aliquet, cursus nisi id, mattis augue. Pellentesque vehicula at ligula vel porta. Fusce suscipit malesuada justo. Cras convallis odio nec dolor elementum facilisis. Donec vel lobortis felis, ut gravida risus. Vivamus interdum ex libero. Phasellus id pharetra tortor. Mauris euismod convallis augue, sit amet aliquet metus hendrerit ac. Duis mattis leo maximus nisi sagittis, a pulvinar turpis fringilla. Ut pellentesque ligula purus, ut iaculis metus finibus nec. Suspendisse diam felis, aliquam sed nisl at, luctus rhoncus magna. Nullam porttitor neque eget sem sagittis rhoncus. Praesent accumsan fermentum odio, ac pellentesque dui feugiat at. In metus nisl, scelerisque eget velit at, pulvinar placerat ex. ")

        citations = [citation_1, citation_2, citation_3, citation_4, citation_5, ]

        for citation in citations:
            yield citation

    def _get_pubmed_citation_generator(self):
        for citation in self._get_ovid_citation_generator():
            # Convert to PubMed headers
            citation.fields["MH"] = citation.fields["MeSH Subject Headings"]
            del citation.fields["MeSH Subject Headings"]
            citation.fields["PMID"] = citation.fields["Unique Identifier"]
            del citation.fields["Unique Identifier"]
            citation.fields["AB"] = citation.fields["Abstract"]
            del citation.fields["Abstract"]
            yield citation

    def _get_synonym_listing(self):
        synonymlisting = dict()
        synonymlisting["Example Gene A"] = ["Example Gene A",]
        synonymlisting["Example Gene B"] = ["Example Gene B",]
        synonymlisting["Example Gene B2"] = ["Example Gene B2",]
        synonymlisting["Example Gene C"] = ["Example Gene Sym C", "Example Gene C",]
        synonymlisting["Example Gene X"] = ["Example Gene X",]
        return synonymlisting

    def _get_synonym_lookup(self):
        synonymlookup = dict()
        synonymlookup["Example Gene Sym C"] = ["Example Gene C",]
        synonymlookup["Example Gene A"] = ["Example Gene A",]
        synonymlookup["Example Gene B"] = ["Example Gene B",]
        synonymlookup["Example Gene B2"] = ["Example Gene B2",]
        synonymlookup["Example Gene C"] = ["Example Gene C",]
        synonymlookup["Example Gene X"] = ["Example Gene X",]
        return synonymlookup

    def test_count_edges_ovid(self):
        """Unit test the temmpo.browser.matching.countedges function using OVID citation syntax
        args: citations, genelist, synonymlookup, synonymlisting, exposuremesh,
        identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
        results_file_path, results_file_name, file_format=OVID

        Creates an abstracts CSV file

        returns: papercounter, edges, identifiers"""
        citations = self._get_ovid_citation_generator()
        genelist = self._get_genes_list()
        synonymlookup = self._get_synonym_lookup()
        synonymlisting = self._get_synonym_listing()
        exposuremesh = self._get_exposure_list()
        identifiers = dict()
        edges = np.zeros(shape=(6, 6), dtype=np.dtype(int))
        outcomemesh = self._get_outcome_list()
        mediatormesh = self._get_mediator_list()
        mesh_filter = None
        results_file_path = settings.RESULTS_PATH
        results_file_name = "test_count_edges_ovid"
        file_format = OVID

        papercounter, edges, identifiers = countedges(citations, genelist,
                synonymlookup, synonymlisting, exposuremesh,
                identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
                results_file_path, results_file_name, file_format=file_format)

        with open(results_file_path + results_file_name + "_abstracts.csv") as csv_file:
            csv_data = csv_file.readlines()
            self.assertEqual(self._get_abstract_csv_data_validation_issues(csv_data), [])
            self.assertEqual(len(csv_data), 3)
            self.assertTrue("999991\r\n" in csv_data)
            self.assertTrue("999994\r\n" in csv_data)

        # Verify papercounter
        self.assertTrue(type(papercounter), int)
        self.assertEqual(papercounter, 2)

        # Verify identifiers - currently not in use
        self.assertEqual(identifiers, dict())

        # Verify edges - expected matches below:
        #                               Cells ; Fictional MeSH Term A ; Neoplasm Metastasis ;;; Fictional MeSH Term AA ; Fictional MeSH Term C ; Serogroup
        # Example Gene A                0       1                       0                       0                        1                       0
        # Example Gene B                1       0                       1                       1                        0                       1
        # Example Gene B2               0       1                       0                       0                        1                       0
        # Example Gene C                0       1                       0                       0                        1                       0
        # Fictional not found MeSH Term 0       0                       0                       0                        0                       0
        # Fictional MeSH Term B         1       1                       1                       1                        1                       1
        expected_edges = np.array([
            [0,1,0,0,1,0],
            [1,0,1,1,0,1],
            [0,1,0,0,1,0],
            [0,1,0,0,1,0],
            [0,0,0,0,0,0],
            [1,1,1,1,1,1]]
            )
        self.assertTrue(np.array_equal(edges, expected_edges))

        os.remove(results_file_path + results_file_name + "_abstracts.csv")

    def test_count_edges_ovid_with_filter(self):
        """Unit test the temmpo.browser.matching.countedges function using OVID citation syntax
        args: citations, genelist, synonymlookup, synonymlisting, exposuremesh,
        identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
        results_file_path, results_file_name, file_format=OVID

        Creates an abstracts CSV file

        returns: papercounter, edges, identifiers"""
        citations = self._get_ovid_citation_generator()
        genelist = self._get_genes_list()
        synonymlookup = self._get_synonym_lookup()
        synonymlisting = self._get_synonym_listing()
        exposuremesh = self._get_exposure_list()
        identifiers = dict()
        edges = np.zeros(shape=(6, 6), dtype=np.dtype(int))
        outcomemesh = self._get_outcome_list()
        mediatormesh = self._get_mediator_list()
        mesh_filter = "Fictional MeSH Term AA"
        results_file_path = settings.RESULTS_PATH
        results_file_name = "test_count_edges_ovid"
        file_format = OVID

        papercounter, edges, identifiers = countedges(citations, genelist,
                synonymlookup, synonymlisting, exposuremesh,
                identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
                results_file_path, results_file_name, file_format=file_format)

        with open(results_file_path + results_file_name + "_abstracts.csv") as csv_file:
            csv_data = csv_file.readlines()
            self.assertEqual(self._get_abstract_csv_data_validation_issues(csv_data), [])
            self.assertEqual(len(csv_data), 2)
            self.assertTrue("999991\r\n" in csv_data)

        # Verify papercounter
        self.assertTrue(type(papercounter), int)
        self.assertEqual(papercounter, 1)
        # Verify identifiers - currently not in use
        self.assertEqual(identifiers, dict())
        # Verify edges - expected matches below:
        #                               Cells ; Fictional MeSH Term A ; Neoplasm Metastasis ;;; Fictional MeSH Term AA ; Fictional MeSH Term C ; Serogroup
        # Example Gene A                0       0                       0                       0                        0                       0
        # Example Gene B                1       0                       1                       1                        0                       1
        # Example Gene B2               0       0                       0                       0                        0                       0
        # Example Gene C                0       0                       0                       0                        0                       0
        # Fictional not found MeSH Term 0       0                       0                       0                        0                       0
        # Fictional MeSH Term B         1       0                       1                       1                        0                       1
        expected_edges = np.array([
            [0,0,0,0,0,0],
            [1,0,1,1,0,1],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [1,0,1,1,0,1]]
            )
        self.assertTrue(np.array_equal(edges, expected_edges))
        os.remove(results_file_path + results_file_name + "_abstracts.csv")

    def test_count_edges_pub_med(self):
        """Unit test the temmpo.browser.matching.countedges function using PubMed citation syntax.
        citations, genelist, synonymlookup, synonymlisting, exposuremesh,
        identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
        results_file_path, results_file_name, file_format=OVID

        Creates a CSV edge file

                returns: papercounter, edges, identifiers"""
        citations = self._get_pubmed_citation_generator()
        genelist = self._get_genes_list()
        synonymlookup = self._get_synonym_lookup()
        synonymlisting = self._get_synonym_listing()
        exposuremesh = self._get_exposure_list()
        identifiers = dict()
        edges = np.zeros(shape=(6, 6), dtype=np.dtype(int))
        outcomemesh = self._get_outcome_list()
        mediatormesh = self._get_mediator_list()
        mesh_filter = None
        results_file_path = settings.RESULTS_PATH
        results_file_name = "test_count_edges_pub_med"
        file_format = PUBMED

        papercounter, edges, identifiers = countedges(citations, genelist,
                synonymlookup, synonymlisting, exposuremesh,
                identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
                results_file_path, results_file_name, file_format=file_format)
        # Verify CSV file is valid CSV
        # Verify that is has a header
        # Verify that it contains the expected matches and no more
        with open(results_file_path + results_file_name + "_abstracts.csv") as csv_file:
            csv_data = csv_file.readlines()
            self.assertEqual(self._get_abstract_csv_data_validation_issues(csv_data), [])
            self.assertEqual(len(csv_data), 3)
            self.assertTrue("999991\r\n" in csv_data)
            self.assertTrue("999994\r\n" in csv_data)

        # Verify papercounter
        self.assertTrue(type(papercounter), int)
        self.assertEqual(papercounter, 2)

        # Verify edges
        expected_edges = np.array([
            [0,1,0,0,1,0],
            [1,0,1,1,0,1],
            [0,1,0,0,1,0],
            [0,1,0,0,1,0],
            [0,0,0,0,0,0],
            [1,1,1,1,1,1]]
            )
        self.assertTrue(np.array_equal(edges, expected_edges))

        # Verify identifiers - NB: currently not in use
        self.assertEqual(identifiers, dict())

        os.remove(results_file_path + results_file_name + "_abstracts.csv")

    def test_count_edges_pub_med_with_filter(self):
        """Unit test the temmpo.browser.matching.countedges function using PubMed citation syntax.
        citations, genelist, synonymlookup, synonymlisting, exposuremesh,
        identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
        results_file_path, results_file_name, file_format=OVID

        Creates a CSV edge file

                returns: papercounter, edges, identifiers"""
        citations = self._get_pubmed_citation_generator()
        genelist = self._get_genes_list()
        synonymlookup = self._get_synonym_lookup()
        synonymlisting = self._get_synonym_listing()
        exposuremesh = self._get_exposure_list()
        identifiers = dict()
        edges = np.zeros(shape=(6, 6), dtype=np.dtype(int))
        outcomemesh = self._get_outcome_list()
        mediatormesh = self._get_mediator_list()
        mesh_filter = "Fictional MeSH Term AA"
        results_file_path = settings.RESULTS_PATH
        results_file_name = "test_count_edges_pub_med"
        file_format = PUBMED

        papercounter, edges, identifiers = countedges(citations, genelist,
                synonymlookup, synonymlisting, exposuremesh,
                identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
                results_file_path, results_file_name, file_format=file_format)
        # Verify CSV file is valid CSV
        # Verify that is has a header
        # Verify that it contains the expected matches and no more
        with open(results_file_path + results_file_name + "_abstracts.csv") as csv_file:
            csv_data = csv_file.readlines()
            self.assertEqual(self._get_abstract_csv_data_validation_issues(csv_data), [])
            self.assertEqual(len(csv_data), 2)
            self.assertTrue("999991\r\n" in csv_data)

        # Verify papercounter
        self.assertTrue(type(papercounter), int)
        self.assertEqual(papercounter, 1)

        #                               Cells ; Fictional MeSH Term A ; Neoplasm Metastasis ;;; Fictional MeSH Term AA ; Fictional MeSH Term C ; Serogroup
        # Example Gene A                0       0                       0                       0                        0                       0
        # Example Gene B                1       0                       1                       1                        0                       1
        # Example Gene B2               0       0                       0                       0                        0                       0
        # Example Gene C                0       0                       0                       0                        0                       0
        # Fictional not found MeSH Term 0       0                       0                       0                        0                       0
        # Fictional MeSH Term B         1       0                       1                       1                        0                       1
        expected_edges = np.array([
            [0,0,0,0,0,0],
            [1,0,1,1,0,1],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [1,0,1,1,0,1]]
            )
        self.assertTrue(np.array_equal(edges, expected_edges))

        # Verify identifiers - NB: currently not in use
        self.assertEqual(identifiers, dict())

        os.remove(results_file_path + results_file_name + "_abstracts.csv")

    def test_ovid_matching_function(self):
        """ovid_mesh_term_text, mesh_term"""
        search_text = ";Cells;;Colorectal Neoplasms/ge [Genetics];;Colorectal Neoplasms/me [Metabolism];;Eryptosis;;Fictional MeSH Term AA;;Fictional MeSH Term B;;Genetic Markers;;Genetic Pleiotropy;;Histamine/me [Metabolism];;Humans;;Male;;*Metabolic Networks and Pathways/ge [Genetics];;*Metabolomics;;Neoplasm Metastasis;;Prostatic Neoplasms/ge [Genetics];;Prostatic Neoplasms/me [Metabolism];;Prostatic Neoplasms/pa [Pathology];;Public Health Systems Research;;Serogroup;;*Transcriptome;"
        mesh_term = "Fictional MeSH Term A"
        self.assertEqual(ovid_matching_function(search_text, mesh_term), None)
        mesh_term = "Fictional MeSH Term AA"
        self.assertTrue(ovid_matching_function(search_text, mesh_term) >= 0)
        mesh_term = "Transcriptome"
        self.assertTrue(ovid_matching_function(search_text, mesh_term) >= 0)
        mesh_term = "Genetics"
        self.assertTrue(ovid_matching_function(search_text, mesh_term) >= 0)

    def test_pubmed_matching_function(self):
        """pubmed_mesh_term_text, mesh_term"""
        search_text = ";Cells;;Colorectal Neoplasms/ge [Genetics];;Colorectal Neoplasms/me [Metabolism];;Eryptosis;;Fictional MeSH Term AA;;Fictional MeSH Term B;;Genetic Markers;;Genetic Pleiotropy;;Histamine/me [Metabolism];;Humans;;Male;;*Metabolic Networks and Pathways/ge [Genetics];;*Metabolomics;;Neoplasm Metastasis;;Prostatic Neoplasms/ge [Genetics];;Prostatic Neoplasms/me [Metabolism];;Prostatic Neoplasms/pa [Pathology];;Public Health Systems Research;;Serogroup;;*Transcriptome;"
        mesh_term = "Fictional MeSH Term A"
        self.assertEqual(pubmed_matching_function(search_text, mesh_term), None)
        mesh_term = "Fictional MeSH Term AA"
        self.assertTrue(pubmed_matching_function(search_text, mesh_term) >= 0)
        mesh_term = "Transcriptome"
        self.assertTrue(pubmed_matching_function(search_text, mesh_term) >= 0)
        mesh_term = "Genetics"
        self.assertTrue(pubmed_matching_function(search_text, mesh_term) >= 0)

    def test_search_gene(self):
        search_text = """A number of preclinical studies have shown that the activation of the vitamin D
      receptor (VDR) reduces prostate cancer (PCa) cell and tumor growth. The majority 
      of human PCas express a transmembrane protease serine 2 (TMPRSS2):erythroblast
      transformation-specific (ETS) fusion gene, but most preclinical studies have been
      performed in PCa models lacking TMPRSS2:ETS in part due to the limited
      availability of model systems expressing endogenous TMPRSS2:ETS. The level of the
      active metabolite of vitamin D, 1alpha,25-dihydroxyvitamin D3 (1,25D), is
      controlled in part by VDR-dependent induction of cytochrome P450, family 24,
      subfamily 1, polypeptide1 (CYP24A1), which metabolizes 1,25D to an inactive form.
      Because ETS factors can cooperate with VDR to induce rat CYP24A1, we tested
      whether TMPRSS2:ETS would cause aberrant induction of human CYP24A1 limiting the 
      activity of VDR. In TMPRSS2:ETS positive VCaP cells, depletion of TMPRSS2:ETS
      substantially reduced 1,25D-mediated CYP24A1 induction. Artificial expression of 
      the type VI+72 TMPRSS2:ETS isoform in LNCaP cells synergized with 1,25D to
      greatly increase CYP24A1 expression. Thus, one of the early effects of
      TMPRSS2:ETS in prostate cells is likely a reduction in intracellular 1,25D, which
      may lead to increased proliferation. Next, we tested the net effect of VDR action
      in TMPRSS2:ETS containing PCa tumors in vivo. Unlike previous animal studies
      performed on PCa tumors lacking TMPRSS2:ETS, EB1089 (seocalcitol) (a less
      calcemic analog of 1,25D) did not inhibit the growth of TMPRSS2:ETS containing
      VCaP tumors in vivo, suggesting that the presence of TMPRSS2:ETS may limit the
      growth inhibitory actions of VDR. Our findings suggest that patients with
      TMPRSS2:ETS negative tumors may be more responsive to VDR-mediated growth
      inhibition and that TMPRSS2:ETS status should be considered in future clinical
      trials."""
        gene = "CYP24A1"
        self.assertTrue(searchgene(search_text, gene) >= 0)
        gene = "TMPRSS2"
        self.assertTrue(searchgene(search_text, gene) >= 0)
        gene = "PRSS10"
        self.assertEqual(searchgene(search_text, gene), None)

    def test_get_genes_and_mediators(self):
        """genelist, mediatormesh"""
        gene_list = [1, 5, 10, 15]
        mediator_list = [2, 4, 6, 8]
        returned_list = _get_genes_and_mediators(gene_list, mediator_list)
        counter = 0
        for item in returned_list:
            if counter == 2:
                self.assertEqual(item, 10)
            if counter == 4:
                self.assertEqual(item, 2)
            if counter == 7:
                self.assertEqual(item, 8)
            counter +=1 
        self.assertEqual(counter, 8)

    def test_printedges(self):
        """edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename"""
        #                               Cells ; Fictional MeSH Term A ; Neoplasm Metastasis |   Fictional MeSH Term AA ; Fictional MeSH Term C ; Serogroup
        # Example Gene A                0       1                       0                   |   0                        1                       0
        # Example Gene B                1       0                       1                   |   1                        0                       1
        # Example Gene B2               0       1                       0                   |   0                        1                       0
        # Example Gene C                0       1                       0                   |   0                        1                       0
        # Fictional not found MeSH Term 0       0                       0                       0                        0                       0
        # Fictional MeSH Term B         1       1                       1                   |   1                        1                       1
        edges = np.array([
            [0,1,0,0,1,0],
            [1,0,1,1,0,1],
            [0,1,0,0,1,0],
            [0,1,0,0,1,0],
            [0,0,0,0,0,0],
            [1,1,1,1,1,1]]
            )
        genelist = self._get_genes_list()
        mediatormesh = self._get_mediator_list()
        exposuremesh = self._get_exposure_list()
        outcomemesh = self._get_outcome_list()
        results_path = settings.RESULTS_PATH
        resultfilename = "test_printedges"
        edge_score = printedges(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename)

        with open(results_path + resultfilename + "_edge.csv", 'rb') as csvfile:
            csv_data = csv.reader(csvfile)
            self.assertEqual(self._get_egde_csv_data_validation_issues(csv_data), [])
            self.assertEqual(edge_score, csv_data.line_num - 1)

        # Tests on Count and Score values
        # score = max(EM,MO) / min(EM,MO) x (EM + MO) from website Help page
        # Expected results
        # Mediator                  Exposure count  Outcome count   Scores  (Not testing as part of data frame as already tested above)
        # Example Gene A            1               1               2
        # Example Gene B            2               2               4
        # Example Gene B2           1               1               2
        # Example Gene C            1               1               2
        # Fictional MeSH Term B     3               3               6
        expected_results = [["Example Gene A", 1, 1, 2],
                            ["Example Gene B", 2, 2, 4],
                            ["Example Gene B2", 1, 1, 2],
                            ["Example Gene C", 1, 1, 2],
                            ["Fictional MeSH Term B", 3, 3, 6]]
        df = pd.read_csv(results_path + resultfilename + "_edge.csv")
        for i in range(0, 5):
            for j in range(0, 4):
                self.assertEqual(expected_results[i][j], df.iat[i, j])
        self.assertEqual(csv_data.line_num, 6)

    def test_createjson(self):
        """edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename

        #                               Cells ; Fictional MeSH Term A ; Neoplasm Metastasis |   Fictional MeSH Term AA ; Fictional MeSH Term C ; Serogroup
        # Example Gene A                0       1                       0                   |   0                        1                       0
        # Example Gene B                1       0                       1                   |   1                        0                       1
        # Example Gene B2               0       1                       0                   |   0                        1                       0
        # Example Gene C                0       1                       0                   |   0                        1                       0
        # Fictional not found MeSH Term 0       0                       0                   |   0                        0                       0
        # Fictional MeSH Term B         1       1                       1                   |   1                        1                       1

        nodes
        0. Example Gene A
        1. Example Gene B
        2. Example Gene B2
        3. Example Gene C
        4. Fictional MeSH Term B
        5. Cells 
        6. Fictional MeSH Term A
        7. Neoplasm Metastasis
        8. Fictional MeSH Term AA
        9. Fictional MeSH Term C
        10. Serogroup

        links
        source  target  value
        6       0       1               Exposure: Cells => Mediator/Gene: Example Gene A
        0       9       1               Mediator/Gene: Example Gene A => Outcome: Fictional MeSH Term C

        5       1       1
        7       1       1
        1       8       1
        1      10       1

        6       2       1
        2       9       1

        6       3       1
        3       9       1

        5       4       1
        6       4       1
        7       4       1
        4       8       1
        4       9       1
        4      10       1
        """
        genelist = self._get_genes_list()
        exposuremesh = self._get_exposure_list()
        edges = np.array([
            [0,1,0,0,1,0],
            [1,0,1,1,0,1],
            [0,1,0,0,1,0],
            [0,1,0,0,1,0],
            [0,0,0,0,0,0],
            [1,1,1,1,1,1]]
            )
        outcomemesh = self._get_outcome_list()
        mediatormesh = self._get_mediator_list()
        results_file_path = settings.RESULTS_PATH
        results_file_name = "test_createjson"
        createjson(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_file_path, results_file_name)
        with open(results_file_path + results_file_name + ".json", 'r') as json_file:
            json_data = json.loads(json_file.read())
            self.assertTrue("nodes" in json_data.keys())
            self.assertTrue("links" in json_data.keys())
            nodes = json_data["nodes"]
            self.assertEqual(len(nodes), 11)        # NB Only lists relevant genes and mediators with matches with at least exposure and at least outcome
            expected_nodes = ["Example Gene A",
                                "Example Gene B",
                                "Example Gene B2",
                                "Example Gene C",
                                "Fictional MeSH Term B",
                                "Cells",
                                "Fictional MeSH Term A",
                                "Neoplasm Metastasis",
                                "Fictional MeSH Term AA",
                                "Fictional MeSH Term C",
                                "Serogroup",]
            for i in range(0, len(expected_nodes)):
                node = nodes[i]
                expected_name = expected_nodes[i]
                self.assertTrue(node.has_key("name"))
                self.assertTrue(node["name"], expected_name)
            links = json_data["links"]
            expected_links = [  {"source":6, "target":0,  "value":1},
                                {"source":0, "target":9,  "value":1},

                                {"source":5, "target":1,  "value":1},
                                {"source":7, "target":1,  "value":1},
                                {"source":1, "target":8,  "value":1},
                                {"source":1, "target":10,  "value":1},

                                {"source":6, "target":2,  "value":1},
                                {"source":2, "target":9,  "value":1},

                                {"source":6, "target":3,  "value":1},
                                {"source":3, "target":9,  "value":1},

                                {"source":5, "target":4,  "value":1},
                                {"source":6, "target":4,  "value":1},
                                {"source":7, "target":4,  "value":1},
                                {"source":4, "target":8,  "value":1},
                                {"source":4, "target":9,  "value":1},
                                {"source":4, "target":10,  "value":1}]
            sorted_expected_links = sorted(expected_links, key=lambda item: (item['source'], item['target']))
            self.assertEqual(len(links), 16)
            sorted_links = sorted(links, key=lambda item: (item['source'], item['target']))
            self.assertEqual(sorted_expected_links, sorted_links)

    def _prepare_gene_matches_only_search_result(self):
        """Generates a search result object and associated edge file

        Mediators,Exposure counts,Outcome counts,Scores
        
        """
        year = 2018
        search_criteria = self._prepare_base_search_criteria(year)

        exposure_term = MeshTerm.objects.get(term="Cells", year=year)
        mediator_term_a = MeshTerm.objects.get(term="Phenotype", year=year)
        mediator_term_b = MeshTerm.objects.get(term="Genetic Markers", year=year)
        outcome_term = MeshTerm.objects.get(term="Public Health Systems Research", year=year)
        gene_list = Gene.objects.filter(name__in=("A1BG", "A2M", "A2MP1", "NAT2", "AAVS1", "LBM180", ))

        search_criteria.genes = gene_list
        search_criteria.exposure_terms.add(exposure_term)
        search_criteria.outcome_terms.add(outcome_term)
        search_criteria.mediator_terms.add(mediator_term_a)
        search_criteria.mediator_terms.add(mediator_term_b)
        search_criteria.mediator_terms.add(mediator_term_a)
        search_criteria.mediator_terms.add(mediator_term_b)
        search_criteria.save()

        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        perform_search(search_result.id)

        return SearchResult.objects.get(id=search_result.id)

    def test_missing_genes_only_mediators(self):
        """"Bug detection - TMMA-377"""
        Gene.objects.all().delete()
        management.call_command('loaddata', 'test_genes_ext.json', verbosity=0)
        search_result = self._prepare_gene_matches_only_search_result()

        with open(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv") as file_obj:
            for line in file_obj:
                logger.debug(line)

        with open(settings.RESULTS_PATH + search_result.filename_stub + ".json") as file_obj:
            parsed = json.load(file_obj)
            logger.debug(json.dumps(parsed, indent=4, sort_keys=True))

        self.assertEqual(search_result.mediator_match_counts_v3, 6)

        with open(settings.RESULTS_PATH + search_result.filename_stub + "_abstracts.csv") as file_obj:
            for line in file_obj:
                logger.debug(line)

    def test_ensure_get_wcrf_input_variables_are_unique_and_sorted(self):
        """"Bug detection - TMMA-377"""
        Gene.objects.all().delete()
        management.call_command('loaddata', 'test_genes_ext.json', verbosity=0)

        year = 2018
        search_criteria = self._prepare_base_search_criteria(year)
        phenotype = MeshTerm.objects.get(term="Phenotype", year=year)
        cells = MeshTerm.objects.get(term="Cells", year=year)
        public_health = MeshTerm.objects.get(term="Public Health Systems Research", year=year)
        search_criteria.exposure_terms.add(phenotype)
        search_criteria.exposure_terms.add(cells)
        search_criteria.exposure_terms.add(cells)
        search_criteria.mediator_terms.add(phenotype)
        search_criteria.mediator_terms.add(phenotype)
        search_criteria.mediator_terms.add(cells)
        search_criteria.outcome_terms.add(public_health)
        search_criteria.outcome_terms.add(cells)
        search_criteria.outcome_terms.add(public_health)
        search_criteria.genes = Gene.objects.filter(name__in=("A1BG", "A2M", "A2MP1", "NAT2", "AAVS1", "LBM180", ))
        self.assertEqual(search_criteria.get_wcrf_input_variables("exposure"), ("Cells", "Phenotype", ))
        self.assertEqual(search_criteria.get_wcrf_input_variables("mediator"), ("Cells", "Phenotype", ))
        self.assertEqual(search_criteria.get_wcrf_input_variables("outcome"), ("Cells", "Public Health Systems Research", ))
        self.assertEqual(search_criteria.get_wcrf_input_variables("gene"), ("A1BG", "A2M", "A2MP1", "AAVS1", "LBM180", "NAT2", ))

    @tag("slow")
    def test_recreate_search_result_630(self):
        """Resolve mismatching: Prostaglandin D2 in MeSH term entries like *Prostaglandin D2/bl [Blood]"""

        MeshTerm.objects.all().delete()
        management.call_command('loaddata', 'mesh_terms_sr_630_2019.json', verbosity=0)
        year = 2019
        exposures = "Basketball; Yoga; Athletic Performance; Bicycling; Circuit-Based Exercise; Water Sports; Boxing; Dancing; Physical Fitness; Breathing Exercises; Warm-Up Exercise; Cool-Down Exercise; Hockey; Dance Therapy; Physical Conditioning, Human; Exercise; Soccer; Football; Endurance Training; Running; Cardiorespiratory Fitness; Baseball; Exercise Therapy; Plyometric Exercise; Track and Field; Racquet Sports; Tennis; Stair Climbing; Weight Lifting; Volleyball; High-Intensity Interval Training; Return to Sport; Jogging; Tai Ji; Motion Therapy, Continuous Passive; Exercise Movement Techniques; Snow Sports; Resistance Training; Sports for Persons with Disabilities; Sports; Physical Endurance; Swimming; Skating; Muscle Stretching Exercises; Walking; Golf; Youth Sports; Wrestling; Mountaineering; Qigong; Gymnastics; Skiing; Diving; Martial Arts"
        mediators = "Prostaglandin D2; Hemorrhagic Septicemia; Carboprost; Macrophage Inflammatory Proteins; alpha-Macroglobulins; Angiotensins; Hemorrhagic Septicemia, Viral; Prostaglandin Endoperoxides; Substance P; Chemokine CXCL9; Autacoids; Chemokine CXCL2; Interferon beta-1a; Fungemia; Chemokine CXCL1; Chemokine CXCL6; Chemokines; Chemokine CXCL5; Interleukin-12 Subunit p40; Ceruloplasmin; Kassinin; Sepsis; Chemokine CCL24; Transforming Growth Factor beta2; Tachykinins; Prostaglandin H2; RANK Ligand; Chemokine CCL17; Macrophage Migration-Inhibitory Factors; Systemic Inflammatory Response Syndrome; Chemokine CCL11; Chemokines, CC; Neurokinin A; Neurokinin B; Chemokine CCL19; Chemokine CCL18; Interleukin-18; OX40 Ligand; Erythropoietin; 1-Sarcosine-8-Isoleucine Angiotensin II; Interleukin-12; Interleukin-13; Interleukin-10; Chemokines, CXC; Interleukin-16; Interleukin-17; Arbaprostil; Interleukin-15; Cyclooxygenase Inhibitors; Prostaglandin Endoperoxides, Synthetic; Lymphokines; Cellulitis; Empyema, Subdural; Kininogen, High-Molecular-Weight; Inflammation; Monokines; CD40 Ligand; Kininogen, Low-Molecular-Weight; Fas Ligand Protein; Neonatal Sepsis; Travoprost; Granulocyte-Macrophage Colony-Stimulating Factor; Fibrinogen; Chemokine CX3CL1; Iloprost; Inflammation Mediators; Angiotensin III; Prostaglandins A, Synthetic; Interleukin-1beta; Macrophage Colony-Stimulating Factor; Tumor Necrosis Factor Ligand Superfamily Member 13; TNF-Related Apoptosis-Inducing Ligand; Monocyte Chemoattractant Proteins; Tumor Necrosis Factor Ligand Superfamily Member 15; Transforming Growth Factor beta1; Bradykinin; Colony-Stimulating Factors; Lenograstim; Transforming Growth Factor beta3; Neurogenic Inflammation; Latanoprost; Epoprostenol; beta-Thromboglobulin; Leukotriene E4; Haptoglobins; Eicosanoids; Leukotriene B4; 4-1BB Ligand; Kininogens; Prostaglandins, Synthetic; Prostaglandins E, Synthetic; Interferons; Interleukin 1 Receptor Antagonist Protein; Seroma; Chemokines, C; Candidemia; Bimatoprost; Fibrinogens, Abnormal; Angiotensin I; C-Reactive Protein; Thrombopoietin; Prostaglandins A; Prostaglandins I; Trypsin Inhibitor, Kazal Pancreatic; Cyclooxygenase 2 Inhibitors; Interleukin-1; Interleukin-12 Subunit p35; Interleukin-33; Serum Amyloid A Protein; Dinoprost; Physalaemin; Macrophage-Activating Factors; Prostaglandins D; Anti-Inflammatory Agents; Prostaglandins E; Leukotriene D4; Parasitemia; alpha 1-Antitrypsin; Anti-Inflammatory Agents, Non-Steroidal; Interferon beta-1b; CD27 Ligand; Transforming Growth Factor beta; Platelet Activating Factor; Chemokine CCL26; Chemokine CCL27; Angiotensin Amide; Leukemia Inhibitory Factor; Chemokine CCL22; Chemokine CCL20; Chemokine CCL21; Bacteremia; Interleukin-2; Interleukin-3; Interleukin-4; Empyema; Interferon-beta; Interleukin-7; Interleukin-8; Interleukin-9; Interferon-gamma; Tumor Necrosis Factors; Oncostatin M; Hemopexin; Serotonin; Interleukin-27; Prostaglandins H; Misoprostol; Osteopontin; Prostaglandins G; Prostaglandins F; Hepatocyte Growth Factor; Implant Capsular Contracture; Prostaglandins B; Viremia; Acute-Phase Proteins; Leukocyte Migration-Inhibitory Factors; Lymphotoxin-alpha; Tumor Necrosis Factor-alpha; Endotoxemia; Leukotriene C4; Alprostadil; Hematopoietic Cell Growth Factors; Ectodysplasins; Chemokine CXCL16; Transferrin; Chemokine CXCL10; Chemokine CXCL11; Chemokine CXCL12; Chemokine CXCL13; Growth Differentiation Factor 15; Interferon Type I; Cloprostenol; Enprostil; Interleukin-23 Subunit p19; Kallidin; Granulocyte Colony-Stimulating Factor; Chemokines, CX3C; Chemokine CCL7; Chemokine CCL5; Chemokine CCL4; Chemokine CCL3; Chemokine CCL2; Chemokine CCL1; Complement C3; Interleukin-1alpha; Shock, Septic; CD30 Ligand; Chemokine CCL8; Suppressor Factors, Immunologic; Abscess; Interleukin-5; Stem Cell Factor; B-Cell Activating Factor; 6-Ketoprostaglandin F1 alpha; SRS-A; Interleukin-23; 15-Hydroxy-11 alpha,9 alpha-(epoxymethano)prosta-5,13-dienoic Acid; Orosomucoid; Acute-Phase Reaction; Interleukins; Interleukin-6; Interleukin-11; Prostaglandins F, Synthetic; Leukotriene A4; Urotensins; Serositis; Demulcents; Saralasin; Eledoisin; Lymphotoxin-beta; Epoetin Alfa; Platelet Factor 4; Foreign-Body Reaction; Interferon-alpha; 16,16-Dimethylprostaglandin E2; Interferon alpha-2; Angiotensin II; Filgrastim; Kinins; Histamine; Lymphotoxin alpha1, beta2 Heterotrimer; Dinoprostone; Serum Amyloid P-Component; Rioprostil; Lipocalin-2; Leukotrienes; Suppuration; Tumor Necrosis Factor Ligand Superfamily Member 14; Cytokines; Transfer Factor; Prostaglandins; alpha 1-Antichymotrypsin; Cytokine TWEAK"
        outcomes = "Breast Neoplasms, Male; Carcinoma, Lobular; Breast Carcinoma In Situ; Breast Neoplasms; Triple Negative Breast Neoplasms; Carcinoma, Ductal, Breast; Hereditary Breast and Ovarian Cancer Syndrome; Unilateral Breast Neoplasms; Inflammatory Breast Neoplasms"
        exposure_list = exposures.split("; ")
        mediator_list = mediators.split("; ")
        outcome_list = outcomes.split("; ")
        filter_term = "Humans"
        # Extract test OVID abstracts and create an upload and search criteria object
        abstract_file_path = os.path.join(BASE_DIR, "07-32-54-exercise-inflamm-breast-cancer-may-3-2019-expanded-terms.txt.gz")
        self._login_user()
        search_path = reverse('search_ovid_medline')
        with open(abstract_file_path, 'r') as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': OVID},
                                        follow=True)
        search_criteria = SearchCriteria.objects.last()
        exposure_terms = MeshTerm.objects.filter(term__in=exposure_list, year=year)
        mediator_terms = MeshTerm.objects.filter(term__in=mediator_list, year=year)
        outcome_terms = MeshTerm.objects.filter(term__in=outcome_list, year=year)
        logger.debug(outcome_terms)
        search_criteria.exposure_terms = exposure_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.outcome_terms = outcome_terms
        search_criteria.year = year
        search_criteria.save()
        search_result = SearchResult(criteria=search_criteria, mesh_filter=filter_term)
        search_result.save()
        perform_search(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)

        # Confirmed can recreate mediator counts in v1
        self.assertTrue(search_result.mediator_match_counts_v3 >= 118)
        
        with open(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv") as edge_csv_file:
            edge_csv_reader = pd.read_csv(edge_csv_file, delimiter=',')
            mediators = edge_csv_reader.loc[: , "Mediators"]
            logger.debug("Mediators")
            logger.debug(mediators)
            self.assertEqual("6-Ketoprostaglandin F1 alpha", mediators[0])
            self.assertEqual("Abscess", mediators[1])
            self.assertEqual("Acute-Phase Proteins", mediators[2])
            self.assertTrue("Prostaglandin D2" in [x for x in mediators])

        # TODO Search results 630 - Assert the v1 ccsv and JSON files created are okay

    @tag('slow', 'insulin')
    def test_verify_missing_insulin_markers(self):
        """TMMA-343 Ensure matching missing IGF-II (Insulin-Like Growth Factor II) and IGFBP-5 (Insulin-Like Growth Factor Binding Protein 5) terms.
            Exposures	Basketball; Yoga; Athletic Performance; Bicycling; Circuit-Based Exercise; Water Sports; Boxing; Dancing; Physical Fitness; Breathing Exercises; Warm-Up Exercise; Cool-Down Exercise; Hockey; Dance Therapy; Physical Conditioning, Human; Exercise; Soccer; Football; Endurance Training; Running; Cardiorespiratory Fitness; Baseball; Exercise Therapy; Plyometric Exercise; Track and Field; Racquet Sports; Tennis; Stair Climbing; Weight Lifting; Volleyball; High-Intensity Interval Training; Return to Sport; Jogging; Tai Ji; Motion Therapy, Continuous Passive; Exercise Movement Techniques; Snow Sports; Resistance Training; Sports for Persons with Disabilities; Sports; Physical Endurance; Swimming; Skating; Muscle Stretching Exercises; Walking; Golf; Youth Sports; Wrestling; Mountaineering; Qigong; Gymnastics; Skiing; Diving; Martial Arts
            Mediators	Insulin, Ultralente; Insulin, Regular, Human; Insulin-Like Growth Factor Binding Protein 1; Insulins; Insulin-Like Growth Factor I; Insulin-Like Growth Factor Binding Protein 6; Insulin Detemir; Insulin-Like Growth Factor Binding Protein 4; Insulin-Like Growth Factor Binding Protein 5; Insulin-Like Growth Factor Binding Protein 2; Insulin-Like Growth Factor Binding Protein 3; C-Peptide; Insulin Lispro; Biphasic Insulins; Insulin, Isophane; Somatomedins; Insulin, Regular, Pork; Insulin, Long-Acting; Isophane Insulin, Human; Insulin Resistance; Nonsuppressible Insulin-Like Activity; Insulin Receptor Substrate Proteins; Proinsulin; Receptor, Insulin; Insulin-Like Growth Factor II; Insulin; Insulin-Like Growth Factor Binding Proteins; Insulin Aspart; Incretins; Insulin Antagonists; Insulin Glargine; Insulin, Short-Acting; Receptor, IGF Type 2; Insulin, Lente; Receptor, IGF Type 1; Metabolic Syndrome; Insulin Secretion
            Outcomes	Breast Neoplasms, Male; Carcinoma, Lobular; Breast Carcinoma In Situ; Breast Neoplasms; Triple Negative Breast Neoplasms; Carcinoma, Ductal, Breast; Hereditary Breast and Ovarian Cancer Syndrome; Unilateral Breast Neoplasms; Inflammatory Breast Neoplasms
            Filter      Humans
            Abstract    08-15-08-insulin-may-27-2019.txt"""

        """Resolve mismatching: Prostaglandin D2 in MeSH term entries like *Prostaglandin D2/bl [Blood]"""

        MeshTerm.objects.all().delete()
        management.call_command('loaddata', 'mesh_terms_sr_650_2019.json', verbosity=0)
        year = 2019
        exposures = "Basketball; Yoga; Athletic Performance; Bicycling; Circuit-Based Exercise; Water Sports; Boxing; Dancing; Physical Fitness; Breathing Exercises; Warm-Up Exercise; Cool-Down Exercise; Hockey; Dance Therapy; Physical Conditioning, Human; Exercise; Soccer; Football; Endurance Training; Running; Cardiorespiratory Fitness; Baseball; Exercise Therapy; Plyometric Exercise; Track and Field; Racquet Sports; Tennis; Stair Climbing; Weight Lifting; Volleyball; High-Intensity Interval Training; Return to Sport; Jogging; Tai Ji; Motion Therapy, Continuous Passive; Exercise Movement Techniques; Snow Sports; Resistance Training; Sports for Persons with Disabilities; Sports; Physical Endurance; Swimming; Skating; Muscle Stretching Exercises; Walking; Golf; Youth Sports; Wrestling; Mountaineering; Qigong; Gymnastics; Skiing; Diving; Martial Arts"
        mediators = "Insulin, Ultralente; Insulin, Regular, Human; Insulin-Like Growth Factor Binding Protein 1; Insulins; Insulin-Like Growth Factor I; Insulin-Like Growth Factor Binding Protein 6; Insulin Detemir; Insulin-Like Growth Factor Binding Protein 4; Insulin-Like Growth Factor Binding Protein 5; Insulin-Like Growth Factor Binding Protein 2; Insulin-Like Growth Factor Binding Protein 3; C-Peptide; Insulin Lispro; Biphasic Insulins; Insulin, Isophane; Somatomedins; Insulin, Regular, Pork; Insulin, Long-Acting; Isophane Insulin, Human; Insulin Resistance; Nonsuppressible Insulin-Like Activity; Insulin Receptor Substrate Proteins; Proinsulin; Receptor, Insulin; Insulin-Like Growth Factor II; Insulin; Insulin-Like Growth Factor Binding Proteins; Insulin Aspart; Incretins; Insulin Antagonists; Insulin Glargine; Insulin, Short-Acting; Receptor, IGF Type 2; Insulin, Lente; Receptor, IGF Type 1; Metabolic Syndrome; Insulin Secretion"
        outcomes = "Breast Neoplasms, Male; Carcinoma, Lobular; Breast Carcinoma In Situ; Breast Neoplasms; Triple Negative Breast Neoplasms; Carcinoma, Ductal, Breast; Hereditary Breast and Ovarian Cancer Syndrome; Unilateral Breast Neoplasms; Inflammatory Breast Neoplasms"
        exposure_list = exposures.split("; ")
        mediator_list = mediators.split("; ")
        outcome_list = outcomes.split("; ")
        filter_term = "Humans"
        # Extract test OVID abstracts and create an upload and search criteria object
        abstract_file_path = os.path.join(BASE_DIR, "08-15-08-insulin-may-27-2019.txt.gz")
        self._login_user()
        search_path = reverse('search_ovid_medline')
        with open(abstract_file_path, 'r') as upload:
            response = self.client.post(search_path,
                                        {'abstracts_upload': upload,
                                         'file_format': OVID},
                                        follow=True)
        search_criteria = SearchCriteria.objects.last()
        exposure_terms = MeshTerm.objects.filter(term__in=exposure_list, year=year)
        mediator_terms = MeshTerm.objects.filter(term__in=mediator_list, year=year)
        outcome_terms = MeshTerm.objects.filter(term__in=outcome_list, year=year)
        logger.debug(outcome_terms)
        search_criteria.exposure_terms = exposure_terms
        search_criteria.mediator_terms = mediator_terms
        search_criteria.outcome_terms = outcome_terms
        search_criteria.year = year
        search_criteria.save()
        search_result = SearchResult(criteria=search_criteria, mesh_filter=filter_term)
        search_result.save()
        perform_search(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)
        
        with open(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv") as edge_csv_file:
            edge_csv_reader = pd.read_csv(edge_csv_file, delimiter=',')
            mediators = edge_csv_reader.loc[: , "Mediators"]
            logger.debug("Mediators")
            for x in mediators:
                logger.debug(x)
            # Confirmed can recreate or surpass mediator counts in v1
            self.assertTrue(search_result.mediator_match_counts_v3 >= 17)
            self.assertTrue("Insulin" in [x for x in mediators])
            self.assertTrue("Insulin-Like Growth Factor I" in [x for x in mediators])
            self.assertTrue("Insulin-Like Growth Factor II" in [x for x in mediators])
            self.assertTrue("Insulin-Like Growth Factor Binding Protein 5" in [x for x in mediators])

    def test_matching_sub_headings(self):
        """Match subheadings such as Blood in *Prostaglandin D2/bl [Blood]"""
        year = 2019
        exposures = "Genetic Markers; Histamine; Eryptosis"
        mediators = "Genetics; Male"
        outcomes = "Prostatic Neoplasms"
        exposure_list = exposures.split("; ")
        mediator_list = mediators.split("; ")
        outcome_list = outcomes.split("; ")
        filter_term = "Humans"
        abstract = u"test-abstract-ovid-test-sample-5.txt"
        search_criteria = self._prepare_base_search_criteria(year, file_name=abstract, file_format=OVID)
        for x in exposure_list:
            search_criteria.exposure_terms.add(MeshTerm.objects.create(term=x, year=year))
        for x in mediator_list:
            search_criteria.mediator_terms.add(MeshTerm.objects.create(term=x, year=year))
        for x in outcome_list:
            search_criteria.outcome_terms.add(MeshTerm.objects.create(term=x, year=year))
        search_criteria.save()
        search_result = SearchResult(criteria=search_criteria, mesh_filter=filter_term)
        search_result.save()
        perform_search(search_result.id)
        search_result = SearchResult.objects.get(id=search_result.id)
        
        with open(settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv") as edge_csv_file:
            edge_csv_reader = pd.read_csv(edge_csv_file, delimiter=',')
            mediators = edge_csv_reader.loc[: , "Mediators"]
            logger.debug(list(mediators))
            self.assertTrue("Genetics" in [x for x in mediators])

        # Matched a sub heading and a standard mesh term heading
        self.assertEqual(search_result.mediator_match_counts_v3, 2)
