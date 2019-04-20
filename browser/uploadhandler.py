import bz2
import gzip
import zipfile

from django.core.files.uploadhandler import FileUploadHandler

COMPRESSION_HANDLRER = {"application/gzip": gzip, 
                        "application/x-bzip": bz2,
                        "application/zip": zipfile,}


class ExtractUpload(FileUploadHandler):

    # self.file_name = None
    # self.content_type = None
    # self.content_length = None
    # self.charset = None
    # self.content_type_extra = None
    # self.request = request

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        """Only enable if file is in an accepted archive format."""
        if self.content_type in COMPRESSION_HANDLRER:
            self.activated = True
        else:
            self.activated = False

    def receive_data_chunk(self, raw_data, start):
        return raw_data

    def file_complete(self, file_size):
        """ return UploadedFile"""
        print("file_complete")
        if not self.activated:
            return

        self.file.seek(0)
        self.file.size = file_size

        # TODO decompress here
        return self.file

    def new_file(self, *args, **kwargs):
        """
        Return a file object if we're activated.
        """
        if not self.activated:
            return None
