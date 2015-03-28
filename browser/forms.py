from django import forms
from browser.models import SearchCriteria, Upload, SearchResult, MeshTerm


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
        print "Exposure clean", cleaned_data, args, kwargs

        if 'term_data' in cleaned_data:
            all_terms = cleaned_data['term_data'].split(',')
            cleaned_data['exposure_terms'] = MeshTerm.objects.filter(tree_number__in = all_terms)

        return cleaned_data

        #data = dict(self.data)
        #print data
        #if 'content' in data:
        #    print data['content']

class MediatorForm(forms.ModelForm):
    class Meta:
        model = SearchCriteria
        fields = ['mediator_terms', 'genes', ]


class OutcomeForm(forms.ModelForm):
    class Meta:
        model = SearchCriteria
        fields = ['outcome_terms', ]


class FilterForm(forms.ModelForm):
    class Meta:
        model = SearchResult
        fields = ['mesh_filter', ]

# TODO create custom form fields widgets
