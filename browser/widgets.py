"""Custom widget field for selecting Gene Filter terms for searches."""

import logging
import sys

from django import forms

from browser.models import Gene

logger = logging.getLogger(__name__)


class GeneTextarea(forms.widgets.Textarea):
    """Base on TextArea widget."""

    def format_value(self, value):
        """Ensure plain text is shown not Gene objects."""
        if not value:
            value = ""

        elif isinstance(value, list):
            # Upon loading search criteria with existing genes saved, widget gets passed a list of Gene objects
            try:
                value = ",".join([gene.name for gene in value])
            except:
                logger.error("Unexpected error handling rendering gene form field: %s", sys.exc_info())

        return super(GeneTextarea, self).format_value(value)
