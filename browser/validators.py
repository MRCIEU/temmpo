import logging
import magic

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class MimetypeValidator(object):
    # ref https://djangosnippets.org/snippets/3039/

    def __init__(self, mimetypes):
        # Expects an iterable list/tuple
        self.mimetypes = mimetypes

    def __call__(self, value):
        try:
            mime = magic.from_buffer(value.read(1024), mime=True)
            if not mime in self.mimetypes:
                raise ValidationError('%s is not an acceptable file type. Please use a %s formatted file instead.' % (value, ' or '.join(self.mimetypes)))
        except AttributeError as e:
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
