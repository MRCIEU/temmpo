import logging
import sys

from django import forms

from browser.models import Gene

logger = logging.getLogger(__name__)


class GeneTextarea(forms.widgets.Textarea):

    def render(self, name, value, attrs=None):
    	# Transform value
    	# Whilst not the nornmal place for this other attempts 
    	# to override field methods are not triggered.
        if not value:
        	value = ""

        elif isinstance(value, list):
            try:
            	# Try to look up list of IDs and turn into Gene names
            	genes = Gene.objects.filter(id__in=value)
            	value = ",".join(genes.values_list('name', flat=True))
            except:
                print "Unexpected error handling rendering gene field:", sys.exc_info()

    	return super(GeneTextarea, self).render(name, value, attrs)
