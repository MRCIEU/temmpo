# -*- coding: utf-8 -*-
import csv
import logging
import math
from more_itertools import unique_everseen
import numpy as np
import os
import pandas as pd
import re
import string
import sys

from django.core.cache import cache
from django.conf import settings
from django.db import connection
# from django.core.mail import send_mail
from django.utils import timezone

from browser.models import SearchResult, Gene, OVID, PUBMED

ERROR_TEXT = b"Error occurred"
logger = logging.getLogger(__name__)
TERM_DELIMITER = b";"


class Citation:
    """Store data as bytes read from user uploaded files"""

    def __init__(self, id):
        self.fields = {}
        self.id = id

    def addfield(self, fieldname):
        self.currentfield = fieldname
        self.fields[fieldname] = b""

    def addfieldcontent(self, fieldcontent):
        self.fields[self.currentfield] += fieldcontent


def perform_search(search_result_stub_id):
    """
    Main function for performing the term search.

    Original structure:
    createsynonyms()
    createedgelist()        Now create_edge_matrix()
    read_citations()
    countedges()
    createresultfile()      No longer in the codebase, was never used in the application.
    printedges()
    createjson()

    """
    logger.info("BEGIN: perform_search on search result: %d" % search_result_stub_id)

    # Get search result
    search_result_stub = SearchResult.objects.get(pk=int(search_result_stub_id))
    search_result_stub.started_processing = timezone.now()
    search_result_stub.has_completed = False
    search_result_stub.save()

    # Get main data
    genelist = search_result_stub.criteria.get_wcrf_input_variables('gene')
    exposuremesh = search_result_stub.criteria.get_wcrf_input_variables('exposure')
    outcomemesh = search_result_stub.criteria.get_wcrf_input_variables('outcome')
    mediatormesh = search_result_stub.criteria.get_wcrf_input_variables('mediator')
    mesh_filter = search_result_stub.mesh_filter or ""  # Previously hard coded to Human then Humans

    # Constants
    WEIGHTFILTER = 2
    GRAPHVIZEDGEMULTIPLIER = 3
    resultfilename = 'results_' + str(search_result_stub.id) + '_' + mesh_filter.replace(" ", "_").lower() + "_topresults"
    results_path = settings.RESULTS_PATH

    logger.debug("Set constants")
    # Get synonyms, edges, identifiers (NOT CURRENTLY IN USE), and citations
    synonymlookup, synonymlisting = cache.get_or_set("temmpo:generate_synonyms", generate_synonyms, timeout=None)
    logger.debug("Done synonyms")

    logger.debug(genelist)
    logger.debug("Exposures")
    logger.debug(exposuremesh)
    logger.debug("Mediators")
    logger.debug(mediatormesh)
    logger.debug("Outcomes")
    logger.debug(outcomemesh)
    edges, identifiers = create_edge_matrix(len(genelist), len(mediatormesh), len(exposuremesh), len(outcomemesh))
    logger.debug("Done edges and TODO: identifiers")

    abstract_file_path = search_result_stub.criteria.upload.abstracts_upload.path
    abstract_file_format = search_result_stub.criteria.upload.file_format
    logger.debug("Read citations START")
    citations = read_citations(file_path=abstract_file_path, file_format=abstract_file_format)
    logger.debug("Read citations END")

    # Count edges
    logger.debug("Count edges START")
    papercounter, edges, identifiers = countedges(citations, genelist,
                                                  synonymlookup, synonymlisting,
                                                  exposuremesh, identifiers,
                                                  edges, outcomemesh,
                                                  mediatormesh, mesh_filter,
                                                  results_path, resultfilename, abstract_file_format)
    logger.debug("Count edges END")

    # Print edges
    logger.debug("Print edges START")
    mediator_match_counts = printedges(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename)
    logger.debug("Printed %s edges", mediator_match_counts)
    logger.debug("Print edges END")

    logger.debug("Create JSON START")
    createjson(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename)
    logger.debug("Create JSON  END")

    # Housekeeping
    # 1 - Mark results done
    search_result_stub.has_completed = True
    search_result_stub.filename_stub = resultfilename
    # 2 - Give end time
    search_result_stub.ended_processing = timezone.now()
    # 3 - Record number of mediator matches
    search_result_stub.mediator_match_counts_v4 = mediator_match_counts
    # X - Email user
    # user_email = search_result_stub.criteria.upload.user.email
    # send_mail('TeMMPo job complete', 'Your TeMMPo search is now complete and the results can be viewed on the TeMMPo web site.', 'webmaster@ilrt.bristol.ac.uk',
    # [user_email,])
    # 4 - Save completed search result
    # NB: Actively refreshing DB connection to handle long processes where the DB connection goes away, only when not in a test.
    if not connection.in_atomic_block:
        logger.debug("Refreshing the connection to the database.")
        connection.close()
    search_result_stub.save()
    # tr.print_diff()
    logger.debug("Done housekeeping")
    logger.info("END: perform_search")

def generate_synonyms():
    """Create dictionaries of synonyms, genes and look ups.
       NB: A synonym can be used for multiple genes.
       ->
       synonymlookup: dict synonym name => list of one or more gene names
       synonymlisting: dict gene name  => list of possible synonyms and itself
    """
    genefile = open(settings.GENE_FILE_LOCATION, 'r')
    synonymlookup = dict()
    synonymlisting = dict()
    for line in genefile:
        line = line.strip().split()
        genename = line[2]
        if line[4] == "-":
            synonyms = []
        else:
            synonyms = line[4].split("|")
        fulllist = synonyms + [genename]
        for synonym in synonyms:
            # TMMA-307 A gene synonym can be an alias for more than one gene.
            matched_gene_names = synonymlookup.get(synonym, [])
            matched_gene_names.append(genename)
            synonymlookup[synonym] = matched_gene_names
        synonymlookup[genename] = [genename, ]
        synonymlisting[genename] = fulllist
    genefile.close()
    return synonymlookup, synonymlisting

def _get_genes_and_mediators(genelist, mediatormesh):
    """Retrieve y axis of matching matrix, genes then mediators"""
    for gene in genelist:
        yield gene

    for mediator in mediatormesh:
        yield mediator

def create_edge_matrix(gene_count, mediator_count, exposure_count, outcome_count):
    """edges represented as a 2D nArray"""
    edges = np.zeros(shape=(gene_count + mediator_count, exposure_count + outcome_count), 
                     dtype=np.dtype(int))
    identifiers = dict()

    return edges, identifiers

def read_citations(file_path, file_format=OVID):
    """ Read the data from either OVID or PUBMED MEDLINE format files """

    if file_format == PUBMED:
        citations = _pubmed_read_citations(file_path)

    elif file_format == OVID:
        citations = _ovid_medline_read_citations(file_path)

    return citations

def _ovid_medline_read_citations(abstract_file_path):
    """ Read the Abstract data from an OVID Medline formatted text file.
        Create a generator and yield an instance of the Citation class per item """
    infile = open(abstract_file_path, 'rb')
    citation = None
    for line in infile:
        line = line.strip(b"\r\n")
        if len(line) == 0:
            pass
        elif line[0:1] == b"<" and line[-1:] == b">" and line.strip(b"<").strip(b">").isdecimal():
            # Starting a new citation, yield if one has already been set up
            if citation:
                yield citation
            citation_id = int(line.strip(b"<").strip(b">"))
            citation = Citation(citation_id)
        elif line[0:1] != b" ":
            citation.addfield(line)
        else:
            if citation.currentfield == b"MeSH Subject Headings":
                citation.addfieldcontent(TERM_DELIMITER + line.lstrip() + TERM_DELIMITER)  # Mesh Terms need clear delimiters not found in Mesh Terms to perform clean matching
            elif citation.currentfield == b"Abstract":
                citation.addfieldcontent(line + b" ")
            else:
                citation.addfieldcontent(line.lstrip())

    # Yield last citation
    if citation:
        yield citation

    infile.close()

def _pubmed_read_citations(abstract_file_path):
    """ Process PubMed MEDLINE formatted abstracts text file
        - code to parse file originally supplied by Benjamin Elsworth

        PubMed MesH term sub headings appear to be lower cased.  Plus any parentheses ()[] are replaced by spaces
        Create a generator and yield an instance of the citation class per item """

    citation = None
    counter = -1
    infile = open(abstract_file_path, 'rb')

    for line in infile:
        line = line.strip(b"\r\n")
        if len(line) == 0 or ERROR_TEXT in line:
            nothing = 0
        elif line[0:4] == b"PMID":
            # Starting a new citation, yield if one has already been set up
            if citation:
                yield citation

            in_mesh = False
            citation_id = counter + 1
            citation = Citation(citation_id)
            counter += 1
            citation.addfield(line.split(b"-", 1)[0].strip())
            citation.addfieldcontent(line.split(b"-", 1)[1].strip())
        elif line[0:2] == b"MH":
            if in_mesh == False:
                citation.addfield(line.split(b"-", 1)[0].strip())
            in_mesh = True
            citation.addfieldcontent(TERM_DELIMITER + line.split(b"-", 1)[1].strip() + TERM_DELIMITER) # Mesh Terms need clear delimiters not found in Mesh Terms to perform clean matching
        elif line[0:1] != b" ":
            field = line.split(b"-", 1)[0].strip()
            citation.addfield(field)
            if field == b"AB":
                citation.addfieldcontent(line.split(b"-", 1)[1] + b" ")
            else:
                citation.addfieldcontent(line.split(b"-", 1)[1].strip() + b" ")
        else:
            citation.addfieldcontent(line.strip() + b" ")

    # Yield last citation
    if citation:
        yield citation

    infile.close()

# TODO: TMM-394 Optimise use of compile for gene matching
def searchgene(texttosearch, searchstring):
    """Return None for no matches >= 0 for match found.
    Gene symbols guidance ref https://www.genenames.org/about/guidelines/#!/#tocAnchor-1-8"""
    searchstringre = re.compile(b'[^A-Za-z0-9#@_]' + re.escape(searchstring).encode() + b'[^A-Za-z0-9#@_]', re.IGNORECASE)
    return searchstringre.search(texttosearch)

def ovid_prepare_mesh_term_search_text_function(mesh_term):
    """Return None for no matches >= 0 for match found.
    NB: An asterisk prefix indicates a major topic of article.
        /?? [Mesh term] denotes sub headings
        ref: http://zatoka.icm.edu.pl/OVIDWEB/fldguide/medline.htm"""
    return re.compile(b'[;*/\\[]' + re.escape(mesh_term).encode() + b'[;/\\]]', re.IGNORECASE)

def pubmed_prepare_mesh_term_search_text_function(mesh_term):
    """Return None for no matches >= 0 for match found.
    NB: An asterisk prefix indicates a major topic of article.
        /mesh term denotes sub headings in lowercase normally
        ref: https://www.nlm.nih.gov/bsd/mms/medlineelements.html#mh"""
    return re.compile(b'[;*/\\[]' + re.escape(mesh_term).encode() + b'[;/\\]]', re.IGNORECASE)  # TODO (Low priority) Performance improvement - Confirm that square braces matching is not needed for PubMED formatted files.

def search_for_mesh_term(mesh_term_search_text, compiled_mesh_term_re):
    return compiled_mesh_term_re.search(mesh_term_search_text)

def countedges(citations, genelist, synonymlookup, synonymlisting, exposuremesh,
               identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
               results_file_path, results_file_name, file_format=OVID):

    # Go through and count edges
    papercounter = 0
    citation_ids_list = list()

    if file_format == OVID:
        unique_id = b"Unique Identifier"
        mesh_subject_headings = b"MeSH Subject Headings"
        abstract = b"Abstract"
        prepare_mesh_term_match_text = ovid_prepare_mesh_term_search_text_function

    elif file_format == PUBMED:
        unique_id = b"PMID"
        mesh_subject_headings = b"MH"
        abstract = b"AB"
        prepare_mesh_term_match_text = pubmed_prepare_mesh_term_search_text_function

    # Prepare dictionary of compiled regular expressions for reuse in mesh term matching
    compiled_mesh_term_reg_exp_hash = {}
    for mesh_term in exposuremesh:
        compiled_mesh_term_reg_exp_hash[mesh_term] = prepare_mesh_term_match_text(mesh_term)
    for mesh_term in mediatormesh:
        compiled_mesh_term_reg_exp_hash[mesh_term] = prepare_mesh_term_match_text(mesh_term)
    for mesh_term in outcomemesh:
        compiled_mesh_term_reg_exp_hash[mesh_term] = prepare_mesh_term_match_text(mesh_term)
    if mesh_filter:
        compiled_mesh_term_reg_exp_hash[mesh_filter] = prepare_mesh_term_match_text(mesh_filter)

    for citation in citations:
        countthis = 0
        edge_row_id = -1
        # Ensure we only test citations with associated mesh headings
        if mesh_subject_headings in citation.fields:
            if not mesh_filter or search_for_mesh_term(citation.fields[mesh_subject_headings], compiled_mesh_term_reg_exp_hash[mesh_filter]) is not None:
                # Only search for genes in citations with an abstract section
                if abstract in citation.fields:
                    for gene in genelist:
                        try:
                            found_gene_match = False
                            edge_row_id += 1
                            edge_column_id = -1
                            # TODO: TMM-394 Optimise generation of gene_matches and synomym_matches - Move outside of citations for loop, include regular expression compile improvements
                            if gene in synonymlookup:
                                gene_matches = synonymlookup[gene]
                            else:
                                gene_matches = (gene, )
                            for gene in gene_matches:
                                if gene in synonymlisting:
                                    synomym_matches = synonymlisting[gene]
                                else:
                                    synomym_matches = (gene, )
                                for genesyn in synomym_matches:
                                    if searchgene(citation.fields[abstract], genesyn) is not None:
                                        citation_ids_list.append(citation.fields[unique_id].strip())
                                        found_gene_match = True
                                        countthis = 1
                                        for exposure in exposuremesh:
                                            edge_column_id += 1
                                            # NB: Removed AND splitting as not possible using the web app interface
                                            if search_for_mesh_term(citation.fields[mesh_subject_headings], compiled_mesh_term_reg_exp_hash[exposure]) is not None:
                                                edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                        for outcome in outcomemesh:
                                            edge_column_id += 1
                                            # NB: Removed AND splitting as not possible using the web app interface
                                            if search_for_mesh_term(citation.fields[mesh_subject_headings], compiled_mesh_term_reg_exp_hash[outcome]) is not None:
                                                edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][1][outcome].append(citation.fields[unique_id])
                                        # Stop comparing synonyms once a match is found
                                        break
                                # Stop comparing synonyms once a match is found
                                if found_gene_match:
                                    break
                        except:
                            # Report unexpected errors
                            logger.warning("Unexpected error handling genes: %s  for gene: %s", (sys.exc_info(), gene, ))

                # Repeat for other mediators
                for mediator in mediatormesh:
                    edge_row_id += 1
                    edge_column_id = -1
                    try:
                        if search_for_mesh_term(citation.fields[mesh_subject_headings], compiled_mesh_term_reg_exp_hash[mediator]) is not None:
                            countthis = 1
                            citation_ids_list.append(citation.fields[unique_id].strip())
                            for exposure in exposuremesh:
                                edge_column_id += 1
                                # NB: Removed AND splitting as not possible using the web app interface
                                if search_for_mesh_term(citation.fields[mesh_subject_headings], compiled_mesh_term_reg_exp_hash[exposure]) is not None:
                                    edges[edge_row_id][edge_column_id] += 1
                                    # identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                            for outcome in outcomemesh:
                                edge_column_id += 1
                                # NB: Removed AND splitting as not possible using the web app interface
                                if search_for_mesh_term(citation.fields[mesh_subject_headings], compiled_mesh_term_reg_exp_hash[outcome]) is not None:
                                    edges[edge_row_id][edge_column_id] += 1
                                    # identifiers[mediator][1][outcome].append(citation.fields[unique_id])
                    except KeyError:
                        # Some citations have no MeSH Terms, so mediator comparisons are not possible
                        # logger.warning("No mesh terms for citation %d" % int(citation.id))
                        pass
                    except:
                        # Report unexpected errors as warning.
                        logger.warning("Unexpected error handling mediator: %s for mediator:%s edge_row_id %s edge_column_id %s", (sys.exc_info(), mediator, edge_row_id, edge_column_id))

        if countthis == 1:
            papercounter += 1

    # Output all citation ids where a gene or mediator MeSH term match is found
    if citation_ids_list:
        resultfile = open('%s%s_abstracts.csv' % (results_file_path, results_file_name), 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(resultfile)
        csv_writer.writerow(("Abstract IDs", ))
        citation_ids_list.reverse()
        # TODO: PYTHON3 Optimise - Change return ordering and whether repeats are shown
        csv_writer.writerows([(cid.decode("utf-8"), ) for cid in unique_everseen(citation_ids_list)])
        resultfile.close()

    return papercounter, edges, identifiers


def printedges(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename):
    """Write out edge file (*_edge.csv)"""
    edgefile = open('%s%s_edge.csv' % (results_path, resultfilename), 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(edgefile)
    csv_writer.writerow(("Mediators", "Exposure counts", "Outcome counts", "Scores",))
    edge_score = 0
    edge_row_id = -1

    for mediator in _get_genes_and_mediators(genelist, mediatormesh):
        edge_col_id = -1
        edge_row_id += 1

        b, d = 0, 0
        for exposure in exposuremesh:
            edge_col_id += 1
            try:
                b += edges[edge_row_id][edge_col_id]
            except:
                b = b
        for outcome in outcomemesh:
            edge_col_id += 1
            try:
                d += edges[edge_row_id][edge_col_id]
            except:
                d = d
        bf, df = float(b), float(d)
        if (bf and df) > 0.0:
            score1 = min(bf, df) / max(bf, df) * (bf + df)
            csv_writer.writerow((mediator, str(b), str(d), str(score1)))
            edge_score += 1

    edgefile.close()

    return edge_score


def createjson(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename):
    """Create JSON formatted resulted file
       TODO - (Low priority improvement) can this be transformed from the CSV more efficiently?"""
    resultfile = open('%s%s.json' % (results_path, resultfilename), 'w', encoding='utf-8')
    nodes = []
    mnodes = []
    edgesout = []
    nodesout = []
    edge_row_id = -1
    # logger.debug("edges")
    # logger.debug(edges)
    for mediator in _get_genes_and_mediators(genelist, mediatormesh):
        edge_col_id = -1
        edge_row_id += 1

        counter = [0, 0]
        for exposure in exposuremesh:
            edge_col_id += 1
            if edges[edge_row_id][edge_col_id] > 0:
                counter[0] += 1
        for outcome in outcomemesh:
            edge_col_id += 1
            if edges[edge_row_id][edge_col_id] > 0:
                counter[1] += 1
        if counter[0] > 0 and counter[1] > 0:
            nodes.append(mediator)
            mnodes.append(mediator)
    for exposure in exposuremesh:
        nodes.append(exposure)
    for outcome in outcomemesh:
        nodes.append(outcome)
    for i in range(len(nodes)):
        thisnode = """{"name":"%s","id":"%d"}""" % (nodes[i], i)
        nodesout.append(thisnode)

    edge_row_id = -1
    for mediator in _get_genes_and_mediators(genelist, mediatormesh):
        edge_col_id = -1
        edge_row_id += 1
        if mediator in mnodes:
            counter = [0, 0]
            for exposure in exposuremesh:
                edge_col_id += 1
                if edges[edge_row_id][edge_col_id] > 0:
                    thisedge = """{"source":%s,"target":%s,"value":%s}""" % (str(nodes.index(exposure)), str(nodes.index(mediator)), str(edges[edge_row_id][edge_col_id]))
                    edgesout.append(thisedge)
                    counter[0] += 1
            for outcome in outcomemesh:
                edge_col_id += 1
                if edges[edge_row_id][edge_col_id] > 0:
                    thisedge = """{"source":%s,"target":%s,"value":%s}""" % (str(nodes.index(mediator)), str(nodes.index(outcome)), str(edges[edge_row_id][edge_col_id]))
                    edgesout.append(thisedge)
                    counter[1] += 1
            if counter[0] == 0:     # TODO: Does this scenario occur? Has it not been dealt with earlier in line 467
                for i in range(counter[1]):
                    edgesout.pop(-1)
            if counter[1] == 0:     # TODO: Does this scenario occur? Has it not been dealt with earlier in line 467
                for i in range(counter[0]):
                    edgesout.pop(-1)
    output = """{"nodes":[%s],"links":[%s]}""" % (",\n".join(nodesout), ",\n".join(edgesout))
    resultfile.write(output)
    resultfile.close()


def record_differences_between_match_runs(search_result_id):
    """Compare edge CSV file for difference.
    Header: Mediators,Exposure counts,Outcome counts,Scores
    v1 unsorted mediators
    v3 mediator column is listed by gene then mesh terms
    v4 mediator column is sorted by gene then mesh terms"""

    search_result = SearchResult.objects.get(id=search_result_id)
    logger.debug("Comparing version 1 to version 3 matching")
    record_differences_between_previous_match_runs(search_result, settings.RESULTS_PATH_V1, settings.RESULTS_PATH_V3, "mediator_match_counts")
    if hasattr(search_result, 'mediator_match_counts_v4'):
        logger.debug("Comparing version 3 to version 4 matching")
        record_differences_between_previous_match_runs(search_result, settings.RESULTS_PATH_V3, settings.RESULTS_PATH_V4, "mediator_match_counts_v3")
    else:
        logger.debug("Version 4 matching field does not yet exist")


def record_differences_between_previous_match_runs(search_result, result_dir_a, result_dir_b, previous_match_counts_field, ):
    """Compare edge CSV file for difference.
       Header: Mediators,Exposure counts,Outcome counts,Scores
    """
    logger.info("START comparing results edge file for %d, e.g. results_%d__topresults_edge.csv" % (search_result.id, search_result.id))
    if getattr(search_result, previous_match_counts_field) is not None:
        result_filepath_a = result_dir_a + search_result.filename_stub + "_edge.csv"
        try:
            logger.info("Read previous CSV edge file %s" % result_filepath_a)
            df_a = pd.read_csv(result_filepath_a,
                                sep=',',
                                header=0,
                                names=("Mediators","Exposure counts","Outcome counts","Scores",),
                                index_col=False,
                                dtype={"Mediators": str,
                                        "Exposure counts": np.int32,
                                        "Outcome counts": np.int32,
                                        "Scores": float,
                                        },
                                engine='python')
            df_a = df_a.sort_values("Mediators")
            result_filepath_b = result_dir_b + search_result.filename_stub + "_edge.csv"
            try:
                logger.info("Read current CSV edge file %s" % result_filepath_b)
                df_b = pd.read_csv(result_filepath_b,
                                    sep=',',
                                    header=0,
                                    names=("Mediators","Exposure counts","Outcome counts","Scores",),
                                    index_col=False,
                                    dtype= {"Mediators": str,
                                            "Exposure counts": np.int32,
                                            "Outcome counts": np.int32,
                                            "Scores": float,
                                            },
                                    engine='python')
                df_b = df_b.sort_values("Mediators")
                is_different = not df_a.equals(df_b)
                if is_different:
                    search_result.has_edge_file_changed = True
                    search_result.save()
                    logger.warning("%d has CHANGED" % search_result.id)
            except IOError as e:
                raise IOError(e)

            except:
                raise

        except IOError as e:
            raise IOError(e)

        except:
            raise
    else:
        logger.info("No previous match results have been recorded for search result %d" % search_result.id)
    logger.info("END comparing results files")
