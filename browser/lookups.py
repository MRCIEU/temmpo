from selectable.base import ModelLookup  #LookupBase
from selectable.registry import registry

from browser.models import MeshTerm


class MeshTermLookup(ModelLookup):
    model = MeshTerm
    search_fields = ('term__icontains', )

    # Reference http://django-selectable.readthedocs.org/en/v0.9.X/lookups.html
    def get_item(self, value):
    	"""We want to return a plain text term value for saving to 
    	SearchResults objects"""
    	return value

registry.register(MeshTermLookup)
