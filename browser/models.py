"""Custom models to facilitate abstracts matching.

NB: Abstract files are not reproduced in the database.  Instead matching is performed from the text files directly.
"""

import re
import unicodedata
import os

from django.db import models
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from mptt.models import MPTTModel, TreeForeignKey


def get_user_upload_location(instance, filename):
    """Based on slugify code - from django.utils.text import slugify."""

    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore')
    filename = unicode(re.sub('[^\.\w\s-]', '', filename).strip().lower())
    filename = re.sub('[-\s]+', '-', filename)

    return timezone.now().strftime('/'.join(['abstracts', str(instance.user.id), '%Y-%m-%d', '%H-%M-%S-' + filename]))


class Gene(models.Model):
    """Prepoulated with genes from the below sources.
    # ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
    # ftp://ftp.ncbi.nih.gov/gene/DATA/README

    Possible alternatives TBC:
    # http://www.genenames.org/cgi-bin/statistics
    # http://www.genenames.org/cgi-bin/genefamilies/download-all/json
    """

    name = models.CharField(max_length=300)
    synonym_for = models.ForeignKey('self', null=True, blank=True, related_name='primary_gene')

    def __str__(self):
        """Create a string version of each Gene."""
        return "Gene: " + self.name


@python_2_unicode_compatible
class MeshTerm(MPTTModel):
    """Pre-populated with MeSH terms from http://www.nlm.nih.gov/mesh/.

    TMMA-131 Root nodes represent the year of release. For example:

    2015
        Anatomy
        Organisms
        ...
    2018
        ...
    """
    term = models.CharField(max_length=300)
    tree_number = models.CharField(max_length=250)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    # TMMA-131 Add year index to speed up searching for terms within a specific year, default 2015
    year = models.PositiveSmallIntegerField(default=2015, db_index=True)

    def __str__(self):
        """Create a string version of each MeshTerm."""
        return self.term

    def get_term_with_details(self):
        """Create a string version of each MeshTerm with tree number."""
        return "Term: %s tree number: %s year: %s" % (self.term, self.tree_number, self.year,)


OVID = 'ovid'
PUBMED = 'pubmed'

ABSTRACT_FORMATS = (
    (OVID, 'Ovid'),
    (PUBMED, 'PubMed'),
)


@python_2_unicode_compatible
class Upload(models.Model):
    """Used to record user uploaded abstract files.

    NB: can be associated with more than one SearchCriteria.
    """

    user = models.ForeignKey(User, null=False, blank=False,
                             related_name="uploads")
    abstracts_upload = models.FileField(upload_to=get_user_upload_location)
    file_format = models.CharField(choices=ABSTRACT_FORMATS, max_length=6, default=OVID)

    def __str__(self):
        """Create a string version of the original Upload file name."""
        return self.filename

    @property
    def filename(self):
        """Helper function to extrapolate only the file name part of an upload."""
        return os.path.basename(self.abstracts_upload.file.name)


class SearchCriteria(models.Model):
    """Used to describe the criteria for a search - which file, which terms, which genes and which filters used."""

    upload = models.ForeignKey(Upload, related_name="searches")
    name = models.CharField(help_text="Optional name for search criteria",
                            max_length=300, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    # TODO: TMMA-244 Add field to record child term selection preference for each _terms fields
    exposure_terms = models.ManyToManyField(MeshTerm,
        verbose_name="exposure MeSH terms", blank=True,
        help_text="Select one or more terms", related_name='sc_exposure')
    outcome_terms = models.ManyToManyField(MeshTerm,
        verbose_name="outcome MeSH terms", blank=True,
        help_text="Select one or more terms", related_name='sc_outcome')
    mediator_terms = models.ManyToManyField(MeshTerm,
        verbose_name="mediator MeSH terms", blank=True,
        help_text="Select one or more terms", related_name='sc_mediator')
    genes = models.ManyToManyField(Gene, blank=True,
        related_name='sc_gene', help_text="Enter one or more gene symbol")
    mesh_terms_year_of_release = models.PositiveSmallIntegerField(default=2015)

    def get_form_codes(self, search_type='exposure'):
        """Helper function to return terms in format that suits forms."""
        form_ids = None
        if search_type == 'exposure':
            form_ids = self.exposure_terms.values_list('id', flat=True)
        elif search_type == 'outcome':
            form_ids = self.outcome_terms.values_list('id', flat=True)
        elif search_type == 'mediator':
            form_ids = self.mediator_terms.values_list('id', flat=True)
        elif search_type == 'gene':
            form_ids = self.genes.values_list('id', flat=True)

        if form_ids:
            return ["%s%s" % ('mtid_', id) for id in form_ids]
        else:
            return []

    def get_wcrf_input_variables(self, codename='exposure'):
        """Helper function to return terms in format that suits the matching code."""
        input_variables = None
        if codename == 'exposure':
            input_variables = self.exposure_terms.values_list('term', flat=True)
        elif codename == 'outcome':
            input_variables = self.outcome_terms.values_list('term', flat=True)
        elif codename == 'mediator':
            input_variables = self.mediator_terms.values_list('term', flat=True)
        elif codename == 'gene':
            input_variables = self.genes.values_list('name', flat=True)

        if input_variables:
            return list(set(input_variables))
        else:
            return []

    def __unicode__(self):
        """Provide a flexible method for determining he search criteria's name.

        At present user's cannot assign names to search criteria through the user interface.
        """
        if self.name:
            return self.name
        else:
            return naturaltime(self.created)


class SearchResult(models.Model):
    """This object holds references to the file system files that represent the results of a given search criteria."""

    criteria = models.ForeignKey(SearchCriteria, related_name='search_results')

    # Abstracting out mesh filter and results as more likely to change the filter
    # but use the same set of other search criteria
    mesh_filter = models.CharField("MeSH filter", max_length=300, blank=True, null=True)
    results = models.FileField(blank=True, null=True,)  # JSON file for output
    has_completed = models.BooleanField(default=False)

    # Store the unique part of the results filenames
    filename_stub = models.CharField(max_length=100, blank=True, null=True)
    started_processing = models.DateTimeField(blank=True, null=True)
    ended_processing = models.DateTimeField(blank=True, null=True)
    # mediator_match_counts # TODO TMMA-157 needed to support displaying mediator match count table
