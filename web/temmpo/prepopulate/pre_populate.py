"""Helper function to create Genes based on a supplied or default gene file."""

from browser.models import Gene
from django.conf import settings


def pre_populate_genes():
    """Pre-populate the genes from a file.

    There is a default Homo_sapiens.gene_info file included with the source code
    or a custom file can be supplied.

    NB: genes that are listed as synonyms also appear in their own right
    hence the code to check we don't already have a record.
    wc -l Homo_sapiens.gene_info == 43855
    Gene.objects.filter(synonym_for__exact = None).count() == 43257

    NB: Expect the first line contains headers not gene information.
    """
    genefile = open(settings.GENE_FILE_LOCATION, 'r')

    headers = genefile.readline()
    assert(headers.startswith("#Format:"))

    for line in genefile:
        line = line.strip().split()
        genename = line[2]
        if line[4] == "-":
            synonyms = []
        else:
            synonyms = line[4].split("|")

        # Store gene
        if Gene.objects.filter(name=genename).exists():
            this_gene = Gene.objects.get(name=genename)
        else:
            this_gene = Gene(name=genename)
            this_gene.save()

        # Store gene synonyms
        for synonym in synonyms:
            if not Gene.objects.filter(name=synonym).exists():
                new_synonym = Gene(name=synonym,
                                   synonym_for=this_gene)
                new_synonym.save()

    genefile.close()
