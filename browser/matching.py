import math
import os
import re
import string
import sys
import unicodecsv

from django.conf import settings
# from django.core.mail import send_mail
from django.utils import timezone

from browser.models import SearchResult, Gene, OVID, PUBMED

ERROR_TEXT = "Error occurred"


class citation:

    def __init__(self, ID):
        self.fields = {}
        self.ID = ID

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
    createedgelist()
    readcitations()
    countedges()
    createresultfile()
    printedges()
    createjson()

    """
    # Get search result
    search_result_stub = SearchResult.objects.get(pk=int(search_result_stub_id))

    search_result_stub.started_processing = timezone.now()
    search_result_stub.has_completed = False
    search_result_stub.save()

    # Get main data
    # user = search_result_stub.criteria.upload.user
    # filename_id
    genelist = search_result_stub.criteria.get_wcrf_input_variables('gene')
    exposuremesh = search_result_stub.criteria.get_wcrf_input_variables('exposure')
    outcomemesh = search_result_stub.criteria.get_wcrf_input_variables('outcome')
    mediatormesh = search_result_stub.criteria.get_wcrf_input_variables('mediator')
    mesh_filter = search_result_stub.mesh_filter or ""  # Previously hardcoded to Human then Humans

    # print "GENE", genelist
    # print "EXP", exposuremesh
    # print "OUT", outcomemesh
    # print "MED", mediatormesh

    # Constants
    WEIGHTFILTER = 2
    GRAPHVIZEDGEMULTIPLIER = 3
    resultfilename = 'results_' + str(search_result_stub.id) + '_' + mesh_filter.replace(" ", "_").lower() + "_topresults"
    results_path = settings.RESULTS_PATH

    print "Set constants"
    # Get synonyms, edges and identifiers, citations
    synonymlookup, synonymlisting = generate_synonyms()
    print "Done synonyms"
    edges, identifiers = createedgelist(genelist, synonymlookup, exposuremesh, outcomemesh, mediatormesh)
    print "Done edges and identifiers"

    abstract_file_path = search_result_stub.criteria.upload.abstracts_upload.path
    abstract_file_format = search_result_stub.criteria.upload.file_format
    citations = readcitations(file_path=abstract_file_path, file_format=abstract_file_format)
    print "Read citations"

    # Count edges
    papercounter, edges, identifiers = countedges(citations, genelist,
                                                  synonymlookup, synonymlisting,
                                                  exposuremesh, identifiers,
                                                  edges, outcomemesh,
                                                  mediatormesh, mesh_filter,
                                                  results_path, resultfilename, abstract_file_format)
    print "Counted edges"

    # Create results
    createresultfile(search_result_stub, exposuremesh, outcomemesh, genelist,
                     synonymlookup, edges, WEIGHTFILTER, mediatormesh,
                     mesh_filter, GRAPHVIZEDGEMULTIPLIER, results_path, resultfilename)

    print "Created results"

    # Print edges
    printedges(edges, exposuremesh, outcomemesh, results_path, resultfilename)
    print "Printed edges"

    createjson(edges, exposuremesh, outcomemesh, results_path, resultfilename)
    print "Created JSON"

    # Housekeeping
    # 1 - Mark results done
    search_result_stub.has_completed = True
    search_result_stub.filename_stub = resultfilename
    # 2 - Give end time
    search_result_stub.ended_processing = timezone.now()
    search_result_stub.save()

    # 3 - Email user
    # user_email = search_result_stub.criteria.upload.user.email
    # send_mail('TeMMPo job complete', 'Your TeMMPo search is now complete and the results can be viewed on the TeMMPo web site.', 'webmaster@ilrt.bristol.ac.uk',
    # [user_email,])

    print "Done housekeeping"


def generate_synonyms2():
    """
    Generate a list of gene synonyms
    """

    all_genes = Gene.objects.filter(synonym_for__exact=None)
    synonymlookup = dict()
    synonymlisting = dict()

    for each_gene in all_genes:
        synonymlookup[each_gene.name] = each_gene.name

        # Get synonyms
        all_synonyms = list(Gene.objects.filter(synonym_for=each_gene).values_list('name', flat=True))
        if all_synonyms:
            for syn in all_synonyms:
                synonymlookup[syn] = each_gene.name
            synonymlisting[each_gene.name] = all_synonyms + [each_gene.name]

    # print synonymlookup
    # print synonymlisting
    return synonymlookup, synonymlisting


def generate_synonyms():
    # Create a dictionary of synoynms
    base_dir = os.path.dirname(__file__)
    full_path = "%s%s%s" % (base_dir, '/static/data-files/', 'Homo_sapiens.gene_info')
    genefile = open(full_path, 'r')
    synonymlookup = dict()
    # synonymresults = dict()
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
            synonymlookup[synonym] = genename
        synonymlookup[genename] = genename
        synonymlisting[genename] = fulllist
    genefile.close()
    return synonymlookup, synonymlisting


def createedgelist(genelist, synonymlookup, exposuremesh, outcomemesh, mediatormesh):
    # edges contains a dictionary of edges to be weighted
    edges = dict()
    identifiers = dict()

    for genel in genelist:
        try:
            gene = synonymlookup[genel]
        except:
            gene = genel
        edges[gene] = [{}, {}]
        identifiers[gene] = [{}, {}]
        for exposure in exposuremesh:
            edges[gene][0][exposure] = 0
            identifiers[gene][0][exposure] = []
        for outcome in outcomemesh:
            edges[gene][1][outcome] = 0
            identifiers[gene][1][outcome] = []
    for mediator in mediatormesh:
        edges[mediator] = [{}, {}]
        identifiers[mediator] = [{}, {}]
        for exposure in exposuremesh:
            edges[mediator][0][exposure] = 0
            identifiers[mediator][0][exposure] = []
        for outcome in outcomemesh:
            edges[mediator][1][outcome] = 0
            identifiers[mediator][1][outcome] = []

    return edges, identifiers


def readcitations(file_path, file_format=OVID):
    """ Read the data from either OVID or PUBMED MEDLINE format files """

    if file_format == PUBMED:
        citations = _pubmed_readcitations(file_path)

    elif file_format == OVID:
        citations = _ovid_medline_readcitations(file_path)

    return citations


def _ovid_medline_readcitations(abstract_file_path):
    """ Read the data in as a list of citations (citation class) """
    citations = list()
    counter = -1
    infile = open(abstract_file_path, 'r')

    for line in infile:
        line = line.strip("\r\n")
        if len(line) == 0:
            nothing = 0
        elif line[0] == "<":
            ID = int(line.strip("<").strip(">"))
            citations.append(citation(ID))
            counter += 1
        elif line[0] != " ":
            citations[counter].addfield(line)
        else:
            citations[counter].addfieldcontent(line.lstrip() + " ")
    infile.close()
    return citations


def _pubmed_readcitations(abstract_file_path):
    """ Process PubMed MEDLINE formatted abstracts
        - code to parse file supplied by Benjamin Elsworth"""

    # PubMed MesH term sub headings appear to be lower cased.  Plus any parentheses ()[] are replaced by spaces
    # Read the data in as a list of citations (citation class)
    citations = list()

    counter = -1
    infile = open(abstract_file_path, 'r')
    for line in infile:
        line = line.strip("\r\n")
        # print "line = "+line
        if len(line) == 0 or ERROR_TEXT in line:
            nothing = 0
        elif line[0:4] == "PMID":
            in_mesh = False
            ID = counter + 1
            citations.append(citation(ID))
            counter += 1
            citations[counter].addfield(line.split("-", 1)[0].strip())
            citations[counter].addfieldcontent(line.split("-", 1)[1].strip())
        elif line[0:2] == "MH":
            if in_mesh == False:
                citations[counter].addfield(line.split("-", 1)[0].strip())
            in_mesh = True
            citations[counter].addfieldcontent(line.split("-", 1)[1].strip() + " ")
        elif line[0] != " ":
            citations[counter].addfield(line.split("-", 1)[0].strip())
            citations[counter].addfieldcontent(line.split("-", 1)[1].strip() + " ")
        else:
            citations[counter].addfieldcontent(line.strip() + " ")
    infile.close()

    return citations


def searchgene(texttosearch, searchstring):
    searchstringre = re.compile('[^A-Za-z]' + searchstring + '[^A-Za-z]')
    return searchstringre.search(texttosearch)


def pubmed_matching_function(pubmed_mesh_term_text, mesh_term):
    """ Return -1 for no matches > 0 for match found,
        Need to perform a case insensitive search that replaces ()[] with spaces before comparison """
    # TODO Profile whether these comparisons should be replaced with regular expressions.
    # TODO Move transformation outside of the matching function, as same term is compared many times
    transformed_mesh_term = mesh_term.lower().replace('[', ' ').replace(']', ' ').replace('(', ' ').replace(')', ' ')
    return string.find(pubmed_mesh_term_text.lower(), transformed_mesh_term)

# TODO: Review changing to accept zero indexed matches - may have affected previous live searches
# TODO: Could re-reun searches and email thoses where changes exist


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
        matches = string.find

    elif file_format == PUBMED:
        unique_id = "PMID"
        mesh_subject_headings = "MH"
        abstract = "AB"
        matches = pubmed_matching_function

    for citation in citations:
        countthis = 0
        # TODO optimisation - check Abstract seciton exists sooner
        # TODO: HIGH PRIORITY - > should be >= to capture any zero indexed matches
        # https://docs.python.org/2/library/string.html#string.find

        # Ensure we only test citations with associated mesh headings
        if mesh_subject_headings in citation.fields:
            if not mesh_filter or matches(citation.fields[mesh_subject_headings], mesh_filter) >= 0:
                for gene in genelist:
                    try:
                        gene = synonymlookup[gene]
                        for genesyn in synonymlisting[gene]:
                            if matches(citation.fields[abstract], genesyn) >= 0:
                                citation_id.add(citation.fields[unique_id].strip())
                                if searchgene(citation.fields[abstract], genesyn):
                                    countthis = 1
                                    for exposure in exposuremesh:
                                        exposurel = exposure.split(" AND ")
                                        if len(exposurel) == 2:
                                            if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0:
                                                edges[gene][0][exposure] += 1
                                                identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                        elif len(exposurel) == 3:
                                            if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[2]) >= 0:
                                                edges[gene][0][exposure] += 1
                                                identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                        else:
                                            if matches(citation.fields[mesh_subject_headings], exposure) >= 0:
                                                edges[gene][0][exposure] += 1
                                                identifiers[gene][0][exposure].append(citation.fields[unique_id])
                                    for outcome in outcomemesh:
                                        outcomel = outcome.split(" AND ")
                                        if len(outcomel) > 1:
                                            if matches(citation.fields[mesh_subject_headings], outcomel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], outcomel[1]) >= 0:
                                                edges[gene][1][outcome] += 1
                                                identifiers[gene][1][outcome].append(citation.fields[unique_id])
                                        else:
                                            if matches(citation.fields[mesh_subject_headings], outcome) >= 0:
                                                edges[gene][1][outcome] += 1
                                                identifiers[gene][1][outcome].append(citation.fields[unique_id])
                                    break
                    except KeyError:
                        # Some citations have no Abstract section
                        pass
                    except:
                        # Report unexpected errors
                        print "Unexpected error handling genes:", sys.exc_info()
                        print " for genes:", genelist

                # Repeat for other mediators
                for mediator in mediatormesh:

                    try:
                        if matches(citation.fields[mesh_subject_headings], mediator) >= 0:
                            countthis = 1
                            citation_id.add(citation.fields[unique_id].strip())
                            for exposure in exposuremesh:
                                exposurel = exposure.split(" AND ")
                                if len(exposurel) == 2:
                                    # print "exposurel", exposurel
                                    if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0:
                                        edges[mediator][0][exposure] += 1
                                        identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                                elif len(exposurel) == 3:
                                    if matches(citation.fields[mesh_subject_headings], exposurel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[1]) >= 0 and matches(citation.fields[mesh_subject_headings], exposurel[2]) >= 0:
                                        edges[mediator][0][exposure] += 1
                                        identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                                else:
                                    if matches(citation.fields[mesh_subject_headings], exposure) >= 0:
                                        edges[mediator][0][exposure] += 1
                                        identifiers[mediator][0][exposure].append(citation.fields[unique_id])
                            for outcome in outcomemesh:
                                # print "b"
                                outcomel = outcome.split(" AND ")
                                if len(outcomel) > 1:
                                    if matches(citation.fields[mesh_subject_headings], outcomel[0]) >= 0 and matches(citation.fields[mesh_subject_headings], outcomel[1]) >= 0:
                                        edges[mediator][1][outcome] += 1
                                        identifiers[mediator][1][outcome].append(citation.fields[unique_id])
                                else:
                                    if matches(citation.fields[mesh_subject_headings], outcome) >= 0:
                                        edges[mediator][1][outcome] += 1
                                        identifiers[mediator][1][outcome].append(citation.fields[unique_id])
                            break
                    except KeyError:
                        # Some citations have no Abstract section
                        pass
                    except:
                        # Report unexpected errors
                        print "Unexpected error handling mediator:", sys.exc_info()
                        print " for mediator:", mediator

        if countthis == 1:
            papercounter += 1

    # Output citation ids
    if citation_id:
        resultfile = open('%s%s_abstracts.csv' % (results_file_path, results_file_name), 'w')
        csv_writer = unicodecsv.writer(resultfile)
        csv_writer.writerow(("Abstract IDs", ))
        csv_writer.writerows([(cid, ) for cid in citation_id])
        resultfile.close()

    return papercounter, edges, identifiers


def createresultfile(search_result_stub, exposuremesh, outcomemesh, genelist,
                     synonymlookup, edges, WEIGHTFILTER, mediatormesh,
                     mesh_filter, GRAPHVIZEDGEMULTIPLIER, results_path, resultfilename):
    """Gephi input.
       NB: These files are is not in use in the web application and are not covered by the test suite.
    """

    resultfile = open('%s%s.csv' % (results_path, resultfilename), 'w')

    exposurecounter = {}
    outcomecounter = {}
    for exposure in exposuremesh:
        exposurecounter["_".join(exposure.split())] = 0
    for outcome in outcomemesh:
        outcomecounter["_".join(outcome.split())] = 0
    for genel in genelist:
        thisresult = ""
        exposureandoutcome = [0, 0]
        try:
            gene = synonymlookup[genel]
            for exposure in exposuremesh:
                if edges[gene][0][exposure] > WEIGHTFILTER:
                    exposureprint = "_".join(exposure.split())
                    exposureandoutcome[0] = 1
                    for i in range(edges[gene][0][exposure]):
                        exposurecounter[exposureprint] += 1
                        thisresult += gene + "," + exposureprint + "\n"
            for outcome in outcomemesh:
                if edges[gene][1][outcome] > WEIGHTFILTER:
                    outcomeprint = "_".join(outcome.split())
                    exposureandoutcome[1] = 1
                    for i in range(edges[gene][1][outcome]):
                        outcomecounter[outcomeprint] += 1
                        thisresult += gene + "," + outcomeprint + "\n"
        except:
            nothing = 0
        if exposureandoutcome == [1, 1]:
            resultfile.write(thisresult)
    for mediator in mediatormesh:
        thisresult = ""
        exposureandoutcome = [0, 0]
        try:
            for exposure in exposuremesh:
                if edges[mediator][0][exposure] > WEIGHTFILTER:
                    exposureprint = "_".join(exposure.split())
                    mediatorprint = "_".join(mediator.split())
                    exposureandoutcome[0] = 1
                    for i in range(edges[mediator][0][exposure]):
                        exposurecounter[exposureprint] += 1
                        thisresult += mediatorprint + "," + exposureprint + "\n"
            for outcome in outcomemesh:
                if edges[mediator][1][outcome] > WEIGHTFILTER:
                    outcomeprint = "_".join(outcome.split())
                    mediatorprint = "_".join(mediator.split())
                    exposureandoutcome[1] = 1
                    for i in range(edges[mediator][1][outcome]):
                        outcomecounter[outcomeprint] += 1
                        thisresult += mediatorprint + "," + outcomeprint + "\n"
        except:
            nothing = 0
        if exposureandoutcome == [1, 1]:
            resultfile.write(thisresult)
    for exposure in exposurecounter.keys():
        for i in range(exposurecounter[exposure]):
            resultfile.write("EXPOSURE," + exposure + "\n")
    for outcome in outcomecounter.keys():
        for i in range(outcomecounter[outcome]):
            resultfile.write("OUTCOME," + outcome + "\n")
    resultfile.close()

    # Output GEPHI file
    gvfile = open('%s%s.gv' % (results_path, resultfilename), 'w')
    gvfile.write('digraph prof {\n size="6,4"; ratio = fill; label = "' + mesh_filter + '"; labelloc = "t"; node [style=filled];\n')
    for exposure in exposurecounter.keys():
        gvfile.write('"EXPOSURE" -> "' + exposure + '" [dir=none,penwidth=' + str((int(math.log10(exposurecounter[exposure] + 0.1)) + 1) * GRAPHVIZEDGEMULTIPLIER) + '];\n')
    for genel in genelist:
        thisresult = ""
        exposureandoutcome = [0, 0]
        try:
            gene = synonymlookup[genel]
            for exposure in exposuremesh:
                if edges[gene][0][exposure] > WEIGHTFILTER:
                    exposureprint = "_".join(exposure.split())
                    exposureandoutcome[0] = 1
                    exposurecounter[exposureprint] += 1
                    thisresult += '"' + exposureprint + '" -> "' + gene + '" [dir=none,penwidth=' + str((int(math.log10(edges[gene][0][exposure] + 0.1)) + 1) * GRAPHVIZEDGEMULTIPLIER) + '];\n'
            for outcome in outcomemesh:
                if edges[gene][1][outcome] > WEIGHTFILTER:
                    outcomeprint = "_".join(outcome.split())
                    exposureandoutcome[1] = 1
                    outcomecounter[outcomeprint] += 1
        except:
            nothing = 0
        if exposureandoutcome == [1, 1]:
            gvfile.write(thisresult)
    for mediator in mediatormesh:
        thisresult = ""
        exposureandoutcome = [0, 0]
        try:
            for exposure in exposuremesh:
                if edges[mediator][0][exposure] > WEIGHTFILTER:
                    exposureprint = "_".join(exposure.split())
                    mediatorprint = "_".join(mediator.split())
                    exposureandoutcome[0] = 1
                    exposurecounter[exposureprint] += 1
                    thisresult += '"' + exposureprint + '" -> "' + mediatorprint + '" [dir=none,penwidth=' + str((int(math.log10(edges[mediator][0][exposure] + 0.1)) + 1) * GRAPHVIZEDGEMULTIPLIER) + '];\n'
            for outcome in outcomemesh:
                if edges[mediator][1][outcome] > WEIGHTFILTER:
                    outcomeprint = "_".join(outcome.split())
                    mediatorprint = "_".join(mediator.split())
                    exposureandoutcome[1] = 1
                    outcomecounter[outcomeprint] += 1
        except:
            nothing = 0
        if exposureandoutcome == [1, 1]:
            gvfile.write(thisresult)
    for genel in genelist:
        thisresult = ""
        exposureandoutcome = [0, 0]
        try:
            gene = synonymlookup[genel]
            for exposure in exposuremesh:
                if edges[gene][0][exposure] > WEIGHTFILTER:
                    exposureprint = "_".join(exposure.split())
                    exposureandoutcome[0] = 1
                    exposurecounter[exposureprint] += 1
            for outcome in outcomemesh:
                if edges[gene][1][outcome] > WEIGHTFILTER:
                    outcomeprint = "_".join(outcome.split())
                    exposureandoutcome[1] = 1
                    outcomecounter[outcomeprint] += 1
                    thisresult += '"' + gene + '" -> "' + outcomeprint + '" [dir=none,penwidth=' + str((int(math.log10(edges[gene][1][outcome] + 0.1)) + 1) * GRAPHVIZEDGEMULTIPLIER) + '];\n'
        except:
            nothing = 0
        if exposureandoutcome == [1, 1]:
            gvfile.write(thisresult)
    for mediator in mediatormesh:
        thisresult = ""
        exposureandoutcome = [0, 0]
        try:
            for exposure in exposuremesh:
                if edges[mediator][0][exposure] > WEIGHTFILTER:
                    exposureprint = "_".join(exposure.split())
                    mediatorprint = "_".join(mediator.split())
                    exposureandoutcome[0] = 1
                    exposurecounter[exposureprint] += 1
            for outcome in outcomemesh:
                if edges[mediator][1][outcome] > WEIGHTFILTER:
                    outcomeprint = "_".join(outcome.split())
                    mediatorprint = "_".join(mediator.split())
                    exposureandoutcome[1] = 1
                    outcomecounter[outcomeprint] += 1
                    thisresult += '"' + mediatorprint + '" -> "' + outcomeprint + '" [dir=none,penwidth=' + str((int(math.log10(edges[mediator][1][outcome] + 0.1)) + 1) * GRAPHVIZEDGEMULTIPLIER) + '];\n'
        except:
            nothing = 0
        if exposureandoutcome == [1, 1]:
            gvfile.write(thisresult)
    for outcome in outcomecounter.keys():
        gvfile.write('"' + outcome + '" -> "OUTCOME" [dir=none,penwidth=' + str((int(math.log10(outcomecounter[outcome] + 0.1)) + 1) * GRAPHVIZEDGEMULTIPLIER) + '];\n')
    gvfile.write("}")
    gvfile.close()


def printedges(edges, exposuremesh, outcomemesh, results_path, resultfilename):
    edge_score = []
    # expanded_edge_score = []
    for ikey in edges.keys():
        b, d = 0, 0
        for exposure in exposuremesh:
            try:
                b += edges[ikey][0][exposure]
            except:
                b = b
        for outcome in outcomemesh:
            try:
                d += edges[ikey][1][outcome]
            except:
                d = d
        bf, df = float(b), float(d)
        if (bf and df) > 0.0:
            score1 = min(bf, df) / max(bf, df) * (bf + df)
            edge_score.append((ikey, str(b), str(d), str(score1)),)  # ,score2
            # expanded_edge_score.append((ikey,exposure,outcome,str(score1),) #,score2

        else:
            score1 = "NA"

    # Write out edge file
    edgefile = open('%s%s_edge.csv' % (results_path, resultfilename), 'w')
    csv_writer = unicodecsv.writer(edgefile)
    csv_writer.writerow(("Mediators", "Exposure counts", "Outcome counts", "Scores",))
    csv_writer.writerows(edge_score)
    edgefile.close()

    # edgeexpfile = open('%s%s_edge_expanded.csv' % (results_path,resultfilename),'w')
    # edgeexpfile.write(expanded_edge_score)
    # edgeexpfile.close()


def createjson(edges, exposuremesh, outcomemesh, results_path, resultfilename):

    resultfile = open('%s%s.json' % (results_path, resultfilename), 'w')
    nodes = []
    mnodes = []
    edgesout = []
    nodesout = []
    for ikey in edges.keys():
        counter = [0, 0]
        for exposure in exposuremesh:
            if edges[ikey][0][exposure] > 0:
                counter[0] += 1
        for outcome in outcomemesh:
            if edges[ikey][1][outcome] > 0:
                counter[1] += 1
        if counter[0] > 0 and counter[1] > 0:
            nodes.append(ikey)
            mnodes.append(ikey)
    for exposure in exposuremesh:
        nodes.append(exposure)
    for outcome in outcomemesh:
        nodes.append(outcome)
    for node in nodes:
        thisnode = """{"name":"%s"}""" % node
        nodesout.append(thisnode)
    for ikey in mnodes:
        counter = [0, 0]
        for exposure in exposuremesh:
            if edges[ikey][0][exposure] > 0:
                thisedge = """{"source":%s,"target":%s,"value":%s}""" % (str(nodes.index(exposure)), str(nodes.index(ikey)), str(edges[ikey][0][exposure]))
                edgesout.append(thisedge)
                counter[0] += 1
        for outcome in outcomemesh:
            if edges[ikey][1][outcome] > 0:
                thisedge = """{"source":%s,"target":%s,"value":%s}""" % (str(nodes.index(ikey)), str(nodes.index(outcome)), str(edges[ikey][1][outcome]))
                edgesout.append(thisedge)
                counter[1] += 1
        if counter[0] == 0:
            for i in range(counter[1]):
                edgesout.pop(-1)
        if counter[1] == 0:
            for i in range(counter[0]):
                edgesout.pop(-1)
    output = """{"nodes":[%s],"links":[%s]}""" % (",\n".join(nodesout), ",\n".join(edgesout))
    resultfile.write(output)
    resultfile.close()
