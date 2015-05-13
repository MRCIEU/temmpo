import re

from django import forms
from browser.models import SearchCriteria, Upload, SearchResult, MeshTerm, Gene
from browser.widgets import GeneTextarea

class AbstractFileUploadForm(forms.ModelForm):
    # abstracts = forms.FileField()  # TODO use custom ajax upload form field

    class Meta:
        model = Upload
        fields = ['abstracts_upload', ]


# TODO: Review possible usage of
# http://django-mptt.github.io/django-mptt/forms.html


class ExposureForm(forms.ModelForm):
    term_data = forms.CharField(widget=forms.HiddenInput,
                                required=True)

    selected_tree_root_node_id = forms.CharField(widget=forms.HiddenInput,
                                         required=False)
    btn_submit = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = SearchCriteria
        fields = ['term_data', 'selected_tree_root_node_id','btn_submit']

    def clean(self, *args, **kwargs):
        cleaned_data = super(ExposureForm, self).clean()

        # Not sure this is needed
        if 'term_data' in cleaned_data:
            all_terms = cleaned_data['term_data'].split(',')
            cleaned_data['exposure_terms'] = MeshTerm.objects.filter(tree_number__in = all_terms)

        return cleaned_data


class MediatorForm(forms.ModelForm):
    term_data = forms.CharField(widget=forms.HiddenInput,
                                required=True)

    selected_tree_root_node_id = forms.CharField(widget=forms.HiddenInput,
                                         required=False)
    btn_submit = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = SearchCriteria
        fields = ['term_data', 'selected_tree_root_node_id','btn_submit']

    def clean(self, *args, **kwargs):
        cleaned_data = super(MediatorForm, self).clean()

        # Not sure this is needed now.
        if 'term_data' in cleaned_data:
            all_terms = cleaned_data['term_data'].split(',')
            cleaned_data['mediator_terms'] = MeshTerm.objects.filter(tree_number__in = all_terms)

        return cleaned_data


class OutcomeForm(forms.ModelForm):
    term_data = forms.CharField(widget=forms.HiddenInput,
                                required=True)

    selected_tree_root_node_id = forms.CharField(widget=forms.HiddenInput,
                                         required=False)
    btn_submit = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = SearchCriteria
        fields = ['term_data', 'selected_tree_root_node_id','btn_submit']

    def clean(self, *args, **kwargs):
        cleaned_data = super(OutcomeForm, self).clean()
        print "Outcome clean", cleaned_data, args, kwargs

        # Not sure this is needed now.
        if 'term_data' in cleaned_data:
            all_terms = cleaned_data['term_data'].split(',')
            cleaned_data['outcome_terms'] = MeshTerm.objects.filter(tree_number__in = all_terms)

        return cleaned_data


class FilterForm(forms.ModelForm):
    genes = forms.CharField(widget=GeneTextarea,
                            required=False,
                            label = 'Enter genes (optional)',
                            help_text = 'Separated by commas')

    ex_filter = forms.ChoiceField(widget = forms.Select(),
                                  choices = ([('1','Humans'), ]),
                                  required = False,
                                  label = 'Filter')

    class Meta:
        model = SearchCriteria
        fields = ['genes', 'ex_filter' ]


    def clean_genes(self):
        data = self.cleaned_data['genes']

        # Clean up data
        gene_list = [x.strip() for x in data.split(',')]
        gene_list = [x for x in gene_list if x]

        matched_genes = []
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
                    new_gene = Gene(name = ind_gene)
                    new_gene.save()
                    print "Added gene: ", new_gene.name
                    
#                 else:
#                     matched_genes.append(ind_gene)

#         if len(unmatched_genes) > 0:
#             raise forms.ValidationError("Gene(s) not found in current list of stored genes (from Homo_sapiens.gene_info): %s" % ",".join(unmatched_genes))

        return ','.join(gene_list)

    def save(self, commit=True):

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

# TODO create custom form fields widgets
