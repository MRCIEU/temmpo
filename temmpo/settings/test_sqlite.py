"""Test specific settings file, currently used in BitBucket pipelines."""

from base import *

# Define a local SQLite database to run tests with
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/usr/local/projects/temmpo/var/data/db.sqlite3',
    }
}
