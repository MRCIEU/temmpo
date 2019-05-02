import bz2
import gzip
import magic
import os
import tempfile

from django import forms
from django.core.files.uploadedfile import TemporaryUploadedFile


class ExtractorFileField(forms.FileField):


    def create_upload_file(self, file):
        size = os.path.getsize(file.name)
        # Intentionally leave file open for continued processing
        file = open(file.name) # TODO review if cannot be opened better in the first place, see w+b

        upload_file = TemporaryUploadedFile(file.name, None, size, file.encoding, None)
        upload_file.file = file

        return upload_file 

    def to_python(self, value):
        value = super(ExtractorFileField, self).to_python(value)
        mime_type = magic.from_buffer(value.read(1024), mime=True)
        if mime_type == "application/x-bzip2":
            file_path = value.temporary_file_path()

            try:
                # Extract archive file to a new file
                with bz2.BZ2File(file_path, 'rb') as file, open(file_path + u"extract", 'wb') as extracted_file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        extracted_file.write(data)
                # Return a new TemporaryUploadedFile of the extracted file
                return self.create_upload_file(extracted_file)

            except Exception as e:
                print("Cannot extract bz2")
                print(e)
                raise forms.ValidationError("There were problems extracting your bz2 file")

        elif mime_type in ("application/x-gzip", "application/gzip"):
            file_path = value.temporary_file_path()

            try:
                # Extract archive file to a new file
                with gzip.open(file_path) as file, open(file_path + u"extract", 'wb') as extracted_file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        extracted_file.write(data)
                # Return a new TemporaryUploadedFile of the extracted file
                return self.create_upload_file(extracted_file)

            except Exception as e:
                print("Cannot extract gzip")
                print(e)
                raise forms.ValidationError("There were problems extracting your gz file")

        return value