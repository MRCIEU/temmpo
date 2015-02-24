from django import forms


class AbstractFileUploadForm(forms.Form):
    abstracts = forms.FileField()


class MeshTermSelectorForm(forms.Form):
    pass
