# -*- coding: utf-8 -*-
import logging
import re

from django import forms
from django.db.models import Max
from django.conf import settings
from django.contrib import messages

from browser.fields import ExtractorFileField
from browser.models import SearchCriteria, Upload, MeshTerm, Gene, OVID, PUBMED
from browser.widgets import GeneTextarea
from browser.validators import MimetypeValidator, SizeValidator, OvidMedLineFormatValidator, PubMedFormatValidator

logger = logging.getLogger(__name__)


class OvidMedLineFileUploadForm(forms.ModelForm):
    file_format = forms.CharField(widget=forms.HiddenInput, initial=OVID)
    abstracts_upload = ExtractorFileField(
        validators=[MimetypeValidator(mimetypes=('text/plain', )),
                    SizeValidator(max_size=2000),
                    OvidMedLineFormatValidator(), ],
        help_text="<br />Ovid MEDLINE® formatted plain text or archive file (*.txt, *.bz, *.gz) which includes MeSH Subject Headings. \
                   Example format <a href=\"" + settings.STATIC_URL + "text/example-file-upload.txt\">with MeSH Subject \
                   Headings</a>. Maximum upload file size: 2000 MB.")

    class Meta:
        model = Upload
        fields = ['file_format', 'abstracts_upload', ]


class PubMedFileUploadForm(forms.ModelForm):
    file_format = forms.CharField(widget=forms.HiddenInput, initial=PUBMED)
    abstracts_upload = ExtractorFileField(
        validators=[MimetypeValidator(mimetypes=('text/plain', )),
                    SizeValidator(max_size=2000),
                    PubMedFormatValidator(), ],
        help_text="<br />PubMed® formatted plain text or archive file (*.txt, *.bz, *.gz) which includes MH (Mesh Headers). \
                   Example format <a href=\"" + settings.STATIC_URL + "text/example-file-upload-b.txt\">with MH (Mesh Headers)</a>. \
                   Maximum upload file size: 2000 MB.")

    class Meta:
        model = Upload
        fields = ['file_format', 'abstracts_upload', ]


class TermSelectorForm(forms.ModelForm):
    term_names = forms.CharField(widget=forms.Textarea(),
                                 required=False, label="Bulk replace terms")
    term_tree_ids = forms.CharField(widget=forms.HiddenInput, required=False)
    include_child_nodes = forms.ChoiceField(widget=forms.RadioSelect(),
                                            choices=(('down', 'Yes'), ('undetermined', 'No'),),
                                            label="Select descendent MeSH® terms",
                                            required=False,
                                            initial='down')
    btn_submit = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = SearchCriteria
        fields = ['term_tree_ids', 'btn_submit', 'term_names', 'include_child_nodes', ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.type = kwargs.pop('type', None)
        super(TermSelectorForm, self).__init__(*args, **kwargs)

    def _select_child_nodes_by_id(self, mesh_term_ids):
        mesh_terms = MeshTerm.objects.filter(id__in=mesh_term_ids)
        child_term_ids = []
        for mesh_term in mesh_terms:
            if not mesh_term.is_leaf_node():
                child_term_ids.extend(mesh_term.get_descendants().values_list('id', flat=True))

        mesh_term_ids.extend(child_term_ids)
        # De-duplicate ids
        mesh_term_ids = list(set(mesh_term_ids))
        return mesh_term_ids

    def _select_child_nodes_by_name(self, mesh_term_names):
        mesh_term_ids = []
        child_term_ids = []

        for name in mesh_term_names:
            mesh_terms = MeshTerm.objects.filter(term__iexact=name, year=self.instance.mesh_terms_year_of_release)
            if mesh_terms.count() == 0:
                messages.add_message(self.request, messages.WARNING, '%s: could not be found' % name)
                # raise a validation error versus a message
            else:
                for term in mesh_terms:
                    mesh_term_ids.append(term.id)
                    if not term.is_leaf_node():
                        mesh_term_ids.extend(term.get_descendants().values_list('id', flat=True))

        mesh_term_ids.extend(child_term_ids)
        # De-duplicate ids
        mesh_term_ids = list(set(mesh_term_ids))
        return mesh_term_ids

    def clean(self):
        mesh_term_ids = []
        if self.cleaned_data['btn_submit'] == "replace" and 'term_names' in self.cleaned_data:
            mesh_terms = self.cleaned_data['term_names'].split(';')
            mesh_terms = [x.strip() for x in mesh_terms if x.strip()]

            if self.cleaned_data.get('include_child_nodes', 'undetermined') == 'down':
                # Ensure all child nodes are selected
                mesh_term_ids = self._select_child_nodes_by_name(mesh_terms)
            else:
                # Only extract IDs of specifically listed Mesh Terms and do not include any child terms.
                mesh_term_ids = MeshTerm.objects.filter(term__in=mesh_terms, year=self.instance.mesh_terms_year_of_release).values_list("id", flat=True)

        elif 'term_tree_ids' in self.cleaned_data:
            mesh_term_ids = self.cleaned_data['term_tree_ids'].split(',')
            mesh_term_ids = [int(x[5:]) for x in mesh_term_ids if len(x) > 5]
            if self.cleaned_data.get('include_child_nodes', 'undetermined') == 'down':
                # Ensure all child nodes are selected
                mesh_term_ids = self._select_child_nodes_by_id(mesh_term_ids)

        if mesh_term_ids:
            duplicates = []

            if self.type != 'exposure':
                duplicates.extend(self.instance.exposure_terms.filter(id__in=mesh_term_ids).values_list("id", flat=True))
            if self.type != 'mediator':
                duplicates.extend(self.instance.mediator_terms.filter(id__in=mesh_term_ids).values_list("id", flat=True))
            if self.type != 'outcome':
                duplicates.extend(self.instance.outcome_terms.filter(id__in=mesh_term_ids).values_list("id", flat=True))

            # TODO handle the fact that users can add genes which may conflict with other exposures or outcomes.
            # genes = self.instance.genes.all().values_list("name", flat=True)

            # Stuff pre-processed terms into cleaned data if no duplicates
            if not duplicates:
                self.cleaned_data['mesh_term_ids'] = mesh_term_ids
            else:
                duplicates = list(MeshTerm.objects.filter(id__in=duplicates).values_list("term", flat=True).distinct())
                raise forms.ValidationError(duplicates, code='duplicates')

        return super(TermSelectorForm, self).clean()


class FilterForm(forms.ModelForm):
    """Present a Filter form to allow matching results to be filter by Gene(s) or MeshTerm of the latest release."""

    genes = forms.CharField(widget=GeneTextarea(attrs={'rows': 4}),
                            required=False,
                            label='Enter genes (optional)',
                            help_text='Separated by commas')
    
    # NB: Filtering of terms needs to happen in the class definition when using the form in a browser
    mesh_filter = forms.ModelChoiceField(queryset=MeshTerm.objects.filter(year=MeshTerm.get_latest_mesh_term_release_year()).exclude(parent=None),
                                         required=False,
                                         label='Filter',
                                         help_text="Enter a MeSH Term, e.g. Humans")

    class Meta:
        model = SearchCriteria
        fields = ['genes', 'mesh_filter', ]

    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        # NB: Filtering of terms needs to also happen in the __init__ for the test suite
        self.fields['mesh_filter'].queryset = MeshTerm.objects.filter(year=MeshTerm.get_latest_mesh_term_release_year()).exclude(parent=None)

    def clean_genes(self):
        data = self.cleaned_data['genes']

        # Clean up data
        gene_list = [x.strip() for x in data.split(',')]
        gene_list = [x for x in gene_list if x]

        # matched_genes = []
        unmatched_genes = []

        for ind_gene in gene_list:
            gene_ok = True
            if re.search(r'[^a-zA-z0-9\-]+', ind_gene):
                gene_ok = False
                raise forms.ValidationError("Invalid gene name found. Gene can only be contain a-z, A-Z, 0-9 and the hyphen character: %s" % ind_gene)

            # Shouldn't reach this point if gene not OK
            if gene_ok:
                if not Gene.objects.filter(name__iexact=ind_gene).exists():
                    # Can't find that gene so create it....
                    # Unhappy about this but Tom's code accepts all genes
                    # rather than those from a controlled list as was
                    # originally the case here.
                    unmatched_genes.append(ind_gene)
                    new_gene = Gene(name=ind_gene)
                    new_gene.save()
                    print "Added gene: ", new_gene.name

#                 else:
#                     matched_genes.append(ind_gene)

#         if len(unmatched_genes) > 0:
#             raise forms.ValidationError("Gene(s) not found in current list of stored genes (from Homo_sapiens.gene_info): %s" % ",".join(unmatched_genes))

        return ','.join(gene_list)

    def save(self, commit=True):
        """Custom save method to allow the additional of new Gene names (and other filter terms)."""
        # Clear any existing genes
        self.instance.genes.clear()
        gene_data = self.cleaned_data['genes']

        if gene_data:

            gene_list = gene_data.split(',')

            for ind_gene in gene_list:
                # Genes have already been checked at this point so we need to get
                # the gene object and then add it to the criteria object
                ind_gene = ind_gene.strip()
                this_gene = Gene.objects.get(name__iexact=ind_gene)
                self.instance.genes.add(this_gene)

        return self.instance
