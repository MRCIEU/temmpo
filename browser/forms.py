from django import forms
from browser.models import SearchCriteria, Upload, SearchResult, MeshTerm, Gene


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
        print "Mediator clean", cleaned_data, args, kwargs

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
    genes = forms.CharField(widget=forms.Textarea,
                            required=True,
                            label = 'Enter genes',
                            help_text = 'CSV separated')

    ex_filter = forms.ChoiceField(widget = forms.Select(),
                                  choices = ([('1','Human'), ]),
                                  required = False,
                                  label = 'Filter')

    class Meta:
        model = SearchResult
        fields = ['genes', 'ex_filter' ]


    def clean_genes(self):
        data = self.cleaned_data['genes']

        gene_list = data.split(',')

        for ind_gene in gene_list:
            if not Gene.objects.filter(name__iexact=ind_gene).exists():
                raise forms.ValidationError("Unrecognised gene: %s" % ind_gene)

        return data

# TODO create custom form fields widgets
