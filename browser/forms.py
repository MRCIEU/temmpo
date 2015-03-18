from django import forms
from browser.models import SearchCriteria, Upload, SearchResult


class AbstractFileUploadForm(forms.ModelForm):
    # abstracts = forms.FileField()  # TODO use custom ajax upload form field

    class Meta:
        model = Upload
        fields = ['abstracts_upload', ]


# TODO: Review possible usage of
# http://django-mptt.github.io/django-mptt/forms.html


class ExposureForm(forms.ModelForm):
    class Meta:
        model = SearchCriteria
        fields = ['exposure_terms', ]


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
