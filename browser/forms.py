from django import forms


class AbstractFileUploadForm(forms.Form):
    abstracts = forms.FileField()


class MeshFilterSelectorForm(forms.Form):
    pass
