import autocomplete_light
from browser.models import MeshTerm

# This will generate a MeshTermAutocomplete class
autocomplete_light.register(MeshTerm,
    # Just like in ModelAdmin.search_fields
    search_fields=['^term'],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Term',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 2,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 4,
        # Enable modern-style widget !
        'class': 'modern-style',
    },
)
