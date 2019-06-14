import logging
import math
import numpy as np
import os
import pandas as pd
import re
import string
import sys
import unicodecsv

from django.conf import settings
# from django.core.mail import send_mail
from django.utils import timezone
from django.core.cache import cache

from browser.models import SearchResult, Gene, OVID, PUBMED

ERROR_TEXT = "Error occurred"
logger = logging.getLogger(__name__)
TERM_DELIMITER = ";"

class Citation:

    def __init__(self, id):
        self.fields = {}
        self.id = id

    def addfield(self, fieldname):
        self.currentfield = fieldname
        self.fields[fieldname] = ""

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
    logger.info("BEGIN: perform_search")

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

    edges, identifiers = create_edge_matrix(len(genelist), len(mediatormesh), len(exposuremesh), len(outcomemesh))
    logger.debug("Done edges and identifiers (TODO)")

    abstract_file_path = search_result_stub.criteria.upload.abstracts_upload.path
    abstract_file_format = search_result_stub.criteria.upload.file_format
    citations = read_citations(file_path=abstract_file_path, file_format=abstract_file_format)
    logger.info("Read citations")

    # Count edges
    papercounter, edges, identifiers = countedges(citations, genelist,
                                                  synonymlookup, synonymlisting,
                                                  exposuremesh, identifiers,
                                                  edges, outcomemesh,
                                                  mediatormesh, mesh_filter,
                                                  results_path, resultfilename, abstract_file_format)
    logger.info("Counted edges")

    # Print edges
    mediator_match_counts = printedges(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename)
    logger.info("Printed %s edges", mediator_match_counts)

    createjson(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename)
    logger.info("Created JSON")

    # Housekeeping
    # 1 - Mark results done
    search_result_stub.has_completed = True
    search_result_stub.filename_stub = resultfilename
    # 2 - Give end time
    search_result_stub.ended_processing = timezone.now()
    # 3 - Record number of mediator matches
    search_result_stub.mediator_match_counts_v3 = mediator_match_counts
    # X - Email user
    # user_email = search_result_stub.criteria.upload.user.email
    # send_mail('TeMMPo job complete', 'Your TeMMPo search is now complete and the results can be viewed on the TeMMPo web site.', 'webmaster@ilrt.bristol.ac.uk',
    # [user_email,])
    # 4 - Save completed search result
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

    infile = open(abstract_file_path, 'r')
    citation = None

    for line in infile:
        line = line.strip("\r\n")
        if len(line) == 0:
            pass
        elif line[0] == "<":
            # Starting a new citation, yield if one has already been set up
            if citation:
                yield citation

            citation_id = int(line.strip("<").strip(">"))
            citation = Citation(citation_id)
        elif line[0] != " ":
            citation.addfield(line)
        else:
            if citation.currentfield == "MeSH Subject Headings":
                citation.addfieldcontent(TERM_DELIMITER + line.lstrip() + TERM_DELIMITER)  # Mesh Terms need clear delimiters not found in Mesh Terms to perform clean matching
            else:
                citation.addfieldcontent(line.lstrip() + " ")

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
    infile = open(abstract_file_path, 'r')

    for line in infile:
        line = line.strip("\r\n")
        if len(line) == 0 or ERROR_TEXT in line:
            nothing = 0
        elif line[0:4] == "PMID":
            # Starting a new citation, yield if one has already been set up
            if citation:
                yield citation

            in_mesh = False
            citation_id = counter + 1
            citation = Citation(citation_id)
            counter += 1
            citation.addfield(line.split("-", 1)[0].strip())
            citation.addfieldcontent(line.split("-", 1)[1].strip())
        elif line[0:2] == "MH":
            if in_mesh == False:
                citation.addfield(line.split("-", 1)[0].strip())
            in_mesh = True
            citation.addfieldcontent(TERM_DELIMITER + line.split("-", 1)[1].strip() + TERM_DELIMITER) # Mesh Terms need clear delimiters not found in Mesh Terms to perform clean matching
        elif line[0] != " ":
            citation.addfield(line.split("-", 1)[0].strip())
            citation.addfieldcontent(line.split("-", 1)[1].strip() + " ")
        else:
            citation.addfieldcontent(line.strip() + " ")

    # Yield last citation
    if citation:
        yield citation

    infile.close()

def searchgene(texttosearch, searchstring):
    """Return None for no matches >= 0 for match found.
    Gene symbols guidance ref https://www.genenames.org/about/guidelines/#!/#tocAnchor-1-8"""
    # TODO: (HIGH bug fix) Confirm of a Gene symbol name at start and end of an abstract will still match
    searchstringre = re.compile('[^A-Za-z0-9#@_]' + searchstring + '[^A-Za-z0-9#@_]')
    return searchstringre.search(texttosearch)

def ovid_matching_function(ovid_mesh_term_text, mesh_term):
    """Return None for no matches >= 0 for match found.
    NB: Asterisks indicate a major topic of article"""
    searchstringre = re.compile('[;*]' + mesh_term + '[*;]')
    return searchstringre.search(ovid_mesh_term_text)

def pubmed_matching_function(pubmed_mesh_term_text, mesh_term):
    """Return None for no matches >= 0 for match found.
    NB: Asterisks indicate a major topic of article
    Need to perform a case insensitive search that replaces ()[] with spaces before comparison """
    # TODO: (Low priority improvement) Move transformation outside of the matching function, as same term is compared many times
    transformed_mesh_term = mesh_term.lower().replace('[', ' ').replace(']', ' ').replace('(', ' ').replace(')', ' ')
    searchstringre = re.compile('[;*]' + transformed_mesh_term + '[*;]')
    return searchstringre.search(pubmed_mesh_term_text.lower())

def countedges(citations, genelist, synonymlookup, synonymlisting, exposuremesh,
               identifiers, edges, outcomemesh, mediatormesh, mesh_filter,
               results_file_path, results_file_name, file_format=OVID):

    # Go through and count edges
    papercounter = 0
    citation_id = set()

    if file_format == OVID:
        unique_id = "Unique Identifier"
        mesh_subject_headings = "MeSH Subject Headings"
        abstract = "Abstract"
        matches = ovid_matching_function

    elif file_format == PUBMED:
        unique_id = "PMID"
        mesh_subject_headings = "MH"
        abstract = "AB"
        matches = pubmed_matching_function

    for citation in citations:
        countthis = 0
        edge_row_id = -1
        # TODO: (Low priority improvement) - check Abstract section exists sooner

        # Ensure we only test citations with associated mesh headings
        if mesh_subject_headings in citation.fields:
            if not mesh_filter or matches(citation.fields[mesh_subject_headings], mesh_filter) >= 0:
                for gene in genelist:
                    try:
                        edge_row_id += 1
                        edge_column_id = -1
                        gene_matches = synonymlookup[gene]
                        found_gene_match = False
                        for gene in gene_matches:
                            for genesyn in synonymlisting[gene]:
                                if searchgene(citation.fields[abstract], genesyn) >= 0:
                                    citation_id.add(citation.fields[unique_id].strip())
                                    found_gene_match = True
                                    countthis = 1
                                    for exposure in exposuremesh:
                                        edge_column_id += 1
                                        exposurel = exposure.split(" AND ")
                                        if len(exposurel) == 2:
                                            if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0:
                                                edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                        elif len(exposurel) == 3:
                                            if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[2]) >= 0:
                                                edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                        else:
                                            if matches(citation.fields[mesh_subject_headings], exposure) >= 0:
                                                edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                    for outcome in outcomemesh:
                                        edge_column_id += 1
                                        outcomel = outcome.split(" AND ")
                                        if len(outcomel) > 1:
                                            if matches(citation.fields[mesh_subject_headings], outcomel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], outcomel[1]) >= 0:
                                               edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][1][outcome].append(citation.fields[unique_id])
                                        else:
                                            if matches(citation.fields[mesh_subject_headings], outcome) >= 0:
                                                edges[edge_row_id][edge_column_id] += 1
                                                # identifiers[gene][1][outcome].append(citation.fields[unique_id])
                                    # Stop comparing synonyms once a match is found
                                    break
                            # Stop comparing synonyms once a match is found
                            if found_gene_match:
                                break

                    except KeyError:
                        # Some citations have no Abstract/MeSH Term section, so gene comparisons are not possible
                        pass
                    except:
                        # Report unexpected errors
                        logger.info("Unexpected error handling genes: %s", sys.exc_info())
                        logger.info(" for gene: %s", gene)

                # Repeat for other mediators
                for mediator in mediatormesh:
                    edge_row_id += 1
                    edge_column_id = -1
                    try:
                        if matches(citation.fields[mesh_subject_headings], mediator) >= 0:
                            countthis = 1
                            citation_id.add(citation.fields[unique_id].strip())
                            for exposure in exposuremesh:
                                edge_column_id += 1
                                exposurel = exposure.split(" AND ")
                                if len(exposurel) == 2:
                                    if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0:
                                        edges[edge_row_id][edge_column_id] += 1
                                        # identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                                elif len(exposurel) == 3:
                                    if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[2]) >= 0:
                                        edges[edge_row_id][edge_column_id] += 1
                                        # identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                                else:
                                    if matches(citation.fields[mesh_subject_headings], exposure) >= 0:
                                        edges[edge_row_id][edge_column_id] += 1
                                        # identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                            for outcome in outcomemesh:
                                edge_column_id += 1
                                outcomel = outcome.split(" AND ")
                                if len(outcomel) > 1:
                                    if matches(citation.fields[mesh_subject_headings], outcomel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], outcomel[1]) >= 0:
                                        edges[edge_row_id][edge_column_id] += 1
                                        # identifiers[mediator][1][outcome].append(citation.fields[unique_id])
                                else:
                                    if matches(citation.fields[mesh_subject_headings], outcome) >= 0:
                                        edges[edge_row_id][edge_column_id] += 1
                                        # identifiers[mediator][1][outcome].append(citation.fields[unique_id])
                    except KeyError:
                        # Some citations have no MeSH Terms, so mediator comparisons are not possible
                        pass
                    except:
                        # Report unexpected errors
                        logger.info("edge_row_id %s", edge_row_id)
                        logger.info("edge_column_id %s", edge_column_id)
                        logger.info("Unexpected error handling mediator: %s", sys.exc_info())
                        logger.info(" for mediator:%s", mediator)

        if countthis == 1:
            papercounter += 1

    # Output all citation ids where a gene or mediator MeSH term match is found
    if citation_id:
        resultfile = open('%s%s_abstracts.csv' % (results_file_path, results_file_name), 'w')
        csv_writer = unicodecsv.writer(resultfile)
        csv_writer.writerow(("Abstract IDs", ))
        csv_writer.writerows([(cid, ) for cid in citation_id])
        resultfile.close()

    return papercounter, edges, identifiers


def printedges(edges, genelist, mediatormesh, exposuremesh, outcomemesh, results_path, resultfilename):
    """Write out edge file (*_edge.csv)"""
    edgefile = open('%s%s_edge.csv' % (results_path, resultfilename), 'w')
    csv_writer = unicodecsv.writer(edgefile)
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
    resultfile = open('%s%s.json' % (results_path, resultfilename), 'w')
    nodes = []
    mnodes = []
    edgesout = []
    nodesout = []
    edge_row_id = -1

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
    for node in nodes:
        thisnode = """{"name":"%s"}""" % node
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
            if counter[0] == 0:
                for i in xrange(counter[1]):
                    edgesout.pop(-1)
            if counter[1] == 0:
                for i in xrange(counter[0]):
                    edgesout.pop(-1)
    output = """{"nodes":[%s],"links":[%s]}""" % (",\n".join(nodesout), ",\n".join(edgesout))
    resultfile.write(output)
    resultfile.close()


def record_differences_between_match_runs(search_result_id):
    """Compare edge CSV file for difference.

    Header: Mediators,Exposure counts,Outcome counts,Scores

    v1 unsorted mediators
    v3 mediator column is sorted by gene then mesh terms
    """
    logger.info("START comparing results edge file for %d, e.g. results_%d__topresults_edge.csv" % (search_result_id, search_result_id))
    from browser.models import SearchResult
    search_result = SearchResult.objects.get(id=search_result_id)

    if search_result.mediator_match_counts is not None:
        v1_filepath = settings.RESULTS_PATH_V1 + search_result.filename_stub + "_edge.csv"
        try:
            # NB: V1 files have trailing commas in body rows
            v1_df = pd.read_csv(v1_filepath,
                                sep=',',
                                header=0,
                                names=("Mediators","Exposure counts","Outcome counts","Scores",),
                                index_col=False,
                                dtype= {"Mediators": np.str,
                                        "Exposure counts": np.int32,
                                        "Outcome counts": np.int32,
                                        "Scores": np.float,
                                        },
                                engine='python')
            v1_df = v1_df.sort_values("Mediators")
            v3_filepath = settings.RESULTS_PATH + search_result.filename_stub + "_edge.csv"
            try:
                v3_df = pd.read_csv(v3_filepath,
                                    sep=',',
                                    header=0,
                                    names=("Mediators","Exposure counts","Outcome counts","Scores",),
                                    index_col=False,
                                    dtype= {"Mediators": np.str,
                                            "Exposure counts": np.int32,
                                            "Outcome counts": np.int32,
                                            "Scores": np.float,
                                            },
                                    engine='python')
                v3_df = v3_df.sort_values("Mediators")
                is_different = not v1_df.equals(v3_df)
                if is_different:
                    search_result.has_edge_file_changed = True
                    search_result.save()
                    logger.info("%d has CHANGED" % search_result_id)
            except IOError:
                raise IOError("No version 3 edge file found for search result %d." % search_result_id)

            except:
                raise

        except IOError:
            raise IOError("No previous edge file found for search result %d" % search_result_id)

        except:
            raise
    else:
        logger.info("No previous match results have been recorded for search result %d" % search_result_id)
    logger.info("END comparing results files")
