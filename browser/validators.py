# -*- coding: utf-8 -*-
import logging
import magic
import re

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

OVID_MEDLINE_IDENTIFIER_PATTERN = re.compile(b"^<\d+>")
OVID_MEDLINE_IDENTIFIER_LABEL_PATTERN = re.compile(b"^Unique Identifier")
OVID_MEDLINE_IDENTIFIER_MESH_PATTERN = re.compile(b"^MeSH Subject Headings")

PUBMED_IDENTIFIER_PATTERN = re.compile(b"^PMID- \d+")
PUBMED_IDENTIFIER_MH_PATTERN = re.compile(b"^MH  -")


class MimetypeValidator(object):
    # ref https://djangosnippets.org/snippets/3039/

    def __init__(self, mimetypes):
        # Expects an iterable list/tuple
        self.mimetypes = mimetypes

    def __call__(self, value):
        try:
            mime = magic.from_buffer(value.read(1024), mime=True)
            if mime not in self.mimetypes:
                raise ValidationError('%s is not an acceptable file type. Please use a %s formatted file instead.' % (value, ' or '.join(self.mimetypes)))
        except AttributeError as e:
            logger.debug("AttributeError")
            logger.debug(e)
            raise ValidationError('There is a problem validating %s as a file.' % value)


class SizeValidator(object):

    def __init__(self, max_size):
        # Expects integer in MB
        self.max_size = max_size

    def __call__(self, value):
        if value:
            if value._size > (self.max_size * 1024 * 1024):
                raise ValidationError('%s is too large. Please try to upload a file smaller than %sMB instead.' % (value, self.max_size))
            else:
                return value
        else:
            raise ValidationError("Couldn't read the uploaded file.")


class OvidMedLineFormatValidator(object):
    """ ref: http://www.nlm.nih.gov/pubs/factsheets/dif_med_pub.html
        ref: http://www.ncbi.nlm.nih.gov/books/NBK3827/#pubmedhelp.MeSH_Terms_MH
        example PubMed > MEDLINE formatted files from: http://www.ncbi.nlm.nih.gov/pubmed?term=neoplasms%20AND%20hasabstract
    """

    def __call__(self, value):
        if value:
            value.seek(0)
            first_line = value.readline()
            second_line = value.readline()
            value.seek(0)

            if has_ovid_medline_file_header(first_line, second_line) and has_ovid_medline_mesh_headings(value):
                return value
            else:
                raise ValidationError('This file %s does not appear to be a Ovid MEDLINE® formatted export of journal '
                                      'abstracts with MeSH Subject Headings. This may be because the file uses '
                                      'Windows line endings and not Linux line endings (or a mixture). Most good text '
                                      'editors allow you to re-save a file using Linux line endings.' % value)
        else:
            raise ValidationError("Couldn't read the uploaded file.")


class PubMedFormatValidator(object):
    """ ref: http://www.nlm.nih.gov/pubs/factsheets/dif_med_pub.html
        ref: http://www.ncbi.nlm.nih.gov/books/NBK3827/#pubmedhelp.MeSH_Terms_MH
        example PubMed > MEDLINE formatted files from: http://www.ncbi.nlm.nih.gov/pubmed?term=neoplasms%20AND%20hasabstract
    """

    def __call__(self, value):
        if value:
            value.seek(0)
            first_line = value.readline()
            second_line = value.readline()
            value.seek(0)

            if has_pubmed_file_header(first_line, second_line) and has_pubmed_mh(value):
                return value
            else:
                raise ValidationError('This file %s does not appear to be a PubMed/MEDLINE® formatted export of journal abstracts with MH (MeSH headers).' % value)
        else:
            raise ValidationError("Couldn't read the uploaded file.")


def has_ovid_medline_file_header(first_line, second_line):
    # Very basic test if the file appears to be in the correct format
    # Test first line if <1> or "\<\d\>"
    # Test second line equals: Unique Identifier
    # When extracted file is passed this not openned in binary file mode
    return (OVID_MEDLINE_IDENTIFIER_PATTERN.match(first_line) and
            OVID_MEDLINE_IDENTIFIER_LABEL_PATTERN.match(second_line))


def has_pubmed_file_header(first_line, second_line):
    # First line is blank
    # Second line should be PMID- {number}
    return (not first_line.strip() and
            PUBMED_IDENTIFIER_PATTERN.match(second_line))


def has_ovid_medline_mesh_headings(value):
    """Check entire file for an instance of Mesh Subject Headings"""
    for line in value:
        if OVID_MEDLINE_IDENTIFIER_MESH_PATTERN.match(line):
            return True
    return False


def has_pubmed_mh(value):
    """Check entire file for an instance MH  - prefixed line"""
    for line in value:
        if PUBMED_IDENTIFIER_MH_PATTERN.match(line):
            return True
    return False