import logging
import mimetypes
import os

import filetype
import magic
from xtract import xtract

from django import forms
from django.core.files.uploadedfile import TemporaryUploadedFile

logger = logging.getLogger(__name__)


class ExtractorFileField(forms.FileField):
    """Custom extractor field - extracts using third party module 
    - https://docs.rolln.de/knoppo/xtract/master/index.html"""

    def _create_upload_file_from_path(self, file_path):
        size = os.path.getsize(file_path)
        encoding = "utf-8"
        # Intentionally leave file open for continued processing
        file_obj = open(file_path, 'rb')
        upload_file = TemporaryUploadedFile(name=file_path, content_type="text/plain", size=size, charset=encoding, content_type_extra=None)
        upload_file.file = file_obj
        return upload_file 

    def to_python(self, value):
        value = super(ExtractorFileField, self).to_python(value)
        mime_type = magic.from_buffer(value.read(1024), mime=True)
        if mime_type == None:
            mime_type = filetype.guess(value.temporary_file_path())
            if mime_type == None:
                mime_type, encoding = mimetypes.guess_type(value.temporary_file_path())
                logger.error("DEBUG: Using mimetypes package")
            else:
                mime_type = mime_type.mime
                logger.error("DEBUG: Using filetype package")
        else:
            logger.error("DEBUG: Using magic package")

        logger.error("DEBUG: temp file path %s" % value.temporary_file_path())
        logger.error("DEBUG: mime %s" % mime_type)

        if mime_type in ('application/gzip', 'application/x-gzip', 'application/bzip', 'application/bzip2', 'application/x-bzip', 'application/x-bzip2'):
            try:
                extracted_file_path = xtract(value.temporary_file_path())
                return self._create_upload_file_from_path(extracted_file_path)
            except Exception as e:
                logger.warning("Cannot extract file %s" % e)
                logger.warning("mime type %s" % mime_type)
                raise forms.ValidationError("There were problems extracting your file.")

        return value