import bz2
import gzip
import magic
import os
import tempfile

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

class ExtractorFileField(forms.FileField):

    # def create_temp_file_from_in_memory(self, in_memory_archive):
    #     new_file = tempfile.NamedTemporaryFile()
    #     for data in iter(lambda: in_memory_archive.read(100 * 1024), b''):
    #         new_file.write(data)
    #     return new_file

    def create_upload_file(self, file, is_in_memory):
        size = os.path.getsize(file.name)
        # Intentionally leave file open for continued processing
        file = open(file.name) # TODO review if cannot be opened better in the first place, see w+b

        if is_in_memory:
            # TODO Under testing unused
            upload_file = InMemoryUploadedFile(file, field_name, file.name, None, size, file.encoding, None)
        else:
            upload_file = TemporaryUploadedFile(file.name, None, size, file.encoding, None)
            upload_file.file = file

        return upload_file 

    def to_python(self, value):
        value = super(ExtractorFileField, self).to_python(value)
        mime_type = magic.from_buffer(value.read(1024), mime=True)
        is_in_memory = isinstance(value, InMemoryUploadedFile)
        if mime_type == "application/x-bzip2":
            if is_in_memory:
                print("InMemoryUploadedFile archive extraction is not currently supported")
                raise forms.ValidationError("Archive files below 2.5MB are not currently supported.") # TODO Used settings vslue not hard coded amount

                # # Write in memory file to disk so can extract contents
                # temp_file = self.create_temp_file_from_in_memory(value)
                # file_path = temp_file.name
            # else:
            file_path = value.temporary_file_path()

            try:
                # Extract archive file to a new file
                with bz2.BZ2File(file_path, 'rb') as file, open(file_path + u"extract", 'wb') as extracted_file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        extracted_file.write(data)
                # Return a new TemporaryUploadedFile of the extracted file
                return self.create_upload_file(extracted_file, is_in_memory)

            except Exception as e:
                print("Cannot extract bz2")
                print(e)
                raise forms.ValidationError("There were problems extracting your bz2 file")

        elif mime_type in ("application/x-gzip", "application/gzip"):
            if is_in_memory:
                print("InMemoryUploadedFile archive extraction is not currently supported")
                raise forms.ValidationError("Archive files below 2.5MB are not currently supported.") # TODO Used settings value not hard coded amount
                # # Write in memory file to disk so can extract contents
                # temp_file = self.create_temp_file_from_in_memory(value)
                # file_path = temp_file.name
            # else:
            file_path = value.temporary_file_path()

            try:
                # Extract archive file to a new file
                with gzip.open(file_path) as file, open(file_path + u"extract", 'wb') as extracted_file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        extracted_file.write(data)
                # Return a new TemporaryUploadedFile of the extracted file
                return self.create_upload_file(extracted_file, is_in_memory)

            except Exception as e:
                print("Cannot extract gzip")
                print(e)
                raise forms.ValidationError("There were problems extracting your gz file")

        return value