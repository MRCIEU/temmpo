from datetime import datetime
import re
import unicodedata

from django.db import models
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturaltime

from mptt.models import MPTTModel, TreeForeignKey


def get_user_upload_location(instance, filename):
    # Based on slugify code - from django.utils.text import slugify

    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore')
    filename = unicode(re.sub('[^\.\w\s-]', '', filename).strip().lower())
    filename = re.sub('[-\s]+', '-', filename)

    return datetime.now().strftime('/'.join(['abstracts', str(instance.user.id), '%Y-%m-%d', '%H-%M-%S-' + filename]))


class Gene(models.Model):
    """
    TODO: Pre-populate this lookup table
    # Subset of gene names, possible vocabulary source:
    # ftp://ftp.ncbi.nih.gov/gene/DATA/)? Or only Human Genes
    # ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
    # ftp://ftp.ncbi.nih.gov/gene/DATA/README
    # TBC as a source: http://www.genenames.org/cgi-bin/statistics
    # TBC: http://www.genenames.org/cgi-bin/genefamilies/download-all/json
    """
    name = models.CharField(max_length=300)  # TODO: Confirm maximum length
    synonym_for = models.ForeignKey('self', null=True, blank=True, related_name='primary_gene')


class MeshTerm(MPTTModel):
    """ FUTURE: May generate JSON as a yearly task when mesh terms are updated
        TODO: Pre-populate with entire tree from  http://www.nlm.nih.gov/mesh/
    """
    term = models.CharField(max_length=300)  # TODO: Confirm maximum length
    tree_number = models.CharField(max_length=50)  # TODO: Confirm maximum length
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    def __str__(self):
        return self.term

    # TODO: Should this be an attribute
    def get_term_with_tree_number(self):
        return self.term + ";" + self.tree_number


class Upload(models.Model):
    """ """

    user = models.ForeignKey(User, null=False, blank=False,
                             related_name="uploads")
    abstracts_upload = models.FileField(upload_to=get_user_upload_location)

    def __str__(self):
        return self.abstracts_upload.name


class Abstract(models.Model):
    """ Would be useful for database/python based matching
        Probably need be extended or replaced when using Solr/Spark
        (https://spark.apache.org) / Lucene based matching
        For instance add custom method to the CitationManager to output in
        format that selected search engine consumes

        # NB: Title and other fields are available but not stored nor used
    """

    # NB: Storing each abstracts per user, not aggregating for general use.
    # Review direction of relationship
    upload = models.ForeignKey(Upload, null=False, blank=False,
                               related_name="abstracts")
    citation_id = models.IntegerField("Unique Identifier")
    # TODO: Confirm if matching a denormalised multi line text field is faster
    # suits certain matching modules better
    # TODO Give good relationship names
    headings = models.ForeignKey(MeshTerm, null=False, blank=False)
    abstract = models.TextField("Abstract")


class SearchCriteria(models.Model):

    upload = models.ForeignKey(Upload, related_name="searches")
    name = models.CharField(help_text="Optional name for search criteria",
                            max_length=300, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    # TODO: Review if need to denormalise term data and store in TextField for
    # performance reasons
    exposure_terms = models.ManyToManyField(MeshTerm,
        verbose_name="exposure MeSH terms", blank=True, null=True,
        help_text="Select one or more terms", related_name='+')
    outcome_terms = models.ManyToManyField(MeshTerm,
        verbose_name="outcome MeSH terms", blank=True, null=True,
        help_text="Select one or more terms", related_name='+')
    mediator_terms = models.ManyToManyField(MeshTerm,
        verbose_name="mediator MeSH terms", blank=True, null=True,
        help_text="Select one or more terms", related_name='+')
    # TODO: Decide comma or line delimited, could normalise to look up table as well
    genes = models.ManyToManyField(Gene, blank=True, null=True,
        related_name='+', help_text="Enter one or more gene symbol")

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return naturaltime(self.created)

class SearchResult(models.Model):

    criteria = models.ForeignKey(SearchCriteria)
    # related_name="result"

    # Abstracting out mesh filter and results as more likely to change the filter
    # but use the same set of other search criteria
    # Confirm maximum term length
    mesh_filter = models.CharField("MeSH filter", max_length=300, blank=True, null=True)
    results = models.FileField(blank=True, null=True,)  # JSON file for output
    # mediator_counts # TODO need to support displaying mediator match count table


"""
Should be able to use default Django User without any custom fields

username
password
email
first_name
last_name

However, may want to at least override email EmailField to ensure max_length=254

"""
