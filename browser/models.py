"""Custom models to facilitate abstracts matching.

NB: Abstract files are not reproduced in the database.  Instead matching is performed from the text files directly.
"""

import logging
import re
import unicodedata
import os
import datetime
import glob

from django.db import models
from django.db.models import Max, Q
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings

from mptt.models import MPTTModel, TreeForeignKey

logger = logging.getLogger(__name__)

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

    @classmethod
    def get_latest_mesh_term_release_year(cls):
        """Retrieve the a latest release year or MeshTerms recorded."""
        try:
            data = cls.objects.root_nodes().aggregate(Max('year'))
            return data['year__max']
        except:
            logger.warning("Retuning current year for get_latest_mesh_term_release_year, as exception when querying the database")
            return datetime.datetime.now().year

    @classmethod
    def get_latest_mesh_term_filter_year_term(cls):
        """Retrieve the a latest release year or MeshTerms recorded."""
        year = cls.get_latest_mesh_term_release_year()
        term = cls.objects.get(term=str(year), year=year)
        return term

    @classmethod
    def get_top_level_mesh_terms(cls, year=None):
        """Get a query set of top level classification terms for a specific year."""
        if not year:
            year = cls.get_latest_mesh_term_release_year()
            # TODO handle errors better when no terms for example
        return cls.objects.root_nodes().get(term=str(year)).get_children()

    @classmethod
    def get_mesh_terms_by_year(cls, year=None):
        """Get a tree query set of MeshTerms for a specific year."""
        if not year:
            year = cls.get_latest_mesh_term_release_year()
        return cls.objects.root_nodes().get(term=str(year)).get_descendants(include_self=False)

    @classmethod
    def convert_terms_to_current_year(cls, previous_term_objs, previous_release, current_year):
        """Convert terms between release years."""
        previous_terms = [x.term for x in previous_term_objs]
        return cls.objects.filter(year=current_year).filter(term__in=previous_terms)


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

    def delete(self):
        """ Override delete as we need to delete the file"""
        upload_usage_count = SearchCriteria.objects.filter(upload=self).count()
        if upload_usage_count <= 1:
            # Not associated with more than one search criteria so we delete Upload record and file
            os.remove(self.abstracts_upload.file.name)
            super(Upload, self).delete()


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
            input_variables = self.exposure_terms.order_by('term').values_list('term', flat=True)
        elif codename == 'outcome':
            input_variables = self.outcome_terms.order_by('term').values_list('term', flat=True)
        elif codename == 'mediator':
            input_variables = self.mediator_terms.order_by('term').values_list('term', flat=True)
        elif codename == 'gene':
            input_variables = self.genes.order_by('name').values_list('name', flat=True)

        if input_variables:
            return set(input_variables)
        else:
            return tuple()

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
    results = models.FileField(blank=True, null=True,)  # NOT IN USE
    has_completed = models.BooleanField(default=False)

    # Store the unique part of the results filenames
    filename_stub = models.CharField(max_length=100, blank=True, null=True)
    started_processing = models.DateTimeField(blank=True, null=True)
    ended_processing = models.DateTimeField(blank=True, null=True)
    mediator_match_counts = models.PositiveIntegerField(blank=True, null=True)
    # After a substantial change to the matching code record in separate field for historic comparisons where required.
    mediator_match_counts_v3 = models.PositiveIntegerField(blank=True, null=True)
    has_edge_file_changed = models.BooleanField(default=False)

    # TMMA-288 Store a reference to the job that has been queue for processing, NB: This reference may not persist between 
    # redis restarts and should be used only for information when tracking processing.
    # job_id = models.CharField(max_length=32, blank=True, null=True)

    @property
    def status(self):
        """Property identifying failed jobs"""
        if self.has_failed:
            return "Search failed"
        elif self.has_completed:
            return "Completed"
        elif self.has_started:
            return "Processing (started %s)" % naturaltime(self.started_processing)
        else:
            return "Not started" 

    @property
    def has_started(self):
        """Property identifying failed jobs"""
        if self.started_processing:
            return True
        else:
            return False

    @property
    def has_failed(self):
        """Property identifying failed jobs"""
        if self.has_completed or not self.has_started:
            return False
        else:
            # Still processing?
            # Assume all processing longer than 12hrs is broken?
            now = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            timediff = now - self.started_processing
            if timediff.total_seconds() > (12 * 60 * 60):
                return True
            else:
                return False

    @property
    def is_deletable(self):
        status = True
        if self.has_started and not self.has_completed and not self.has_failed:
            status = False
        return status

    def delete(self):
        """ Override delete as there are a number of things we need to remove"""

        # Try deleting upload
        # Won't be deleted if Upload file is used on more than one search
        upload_record = self.criteria.upload
        upload_record.delete()

        # Delete SearchCriteria
        self.criteria.delete()

        # Delete associated results files (if completed)
        if self.has_completed:
            base_path = settings.RESULTS_PATH + self.filename_stub + '*'
            files_to_delete = glob.glob(base_path)

            for delfile in files_to_delete:
                os.remove(delfile)

        # If version 1 files exists delete as well.
        if self.mediator_match_counts is not None:
            base_path = settings.RESULTS_PATH_V1 + self.filename_stub + '*'
            files_to_delete = glob.glob(base_path)

            for delfile in files_to_delete:
                os.remove(delfile)

        super(SearchResult, self).delete()

    @property
    def has_changed(self):
        return self.has_match_counts_changed or self.has_edge_file_changed

    @property
    def has_match_counts_changed(self):
        return (self.mediator_match_counts is not None and self.mediator_match_counts != self.mediator_match_counts_v3)


class MessageManager(models.Manager):

    def get_current_messages(self):
        return self.filter(is_disabled=False).filter(Q(end__isnull=True) | Q(end__gte=timezone.now())).filter(start__lte=timezone.now()).order_by("start").values_list('body', flat=True)


class Message(models.Model):

    body = models.CharField(max_length=500)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=False, blank=False,
                             related_name="author")

    objects = MessageManager()

    def __unicode__(self):
        if self.body:
            return self.body
        else:
            return naturaltime(self.start)