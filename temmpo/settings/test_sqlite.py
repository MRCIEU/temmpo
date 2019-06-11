"""Test specific settings file, currently used in BitBucket pipelines."""

from base import *

# Define a local SQLite database to run tests with
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/usr/local/projects/temmpo/var/data/db.sqlite3',
    }
}

RQ_QUEUES['default']['ASYNC'] = False
LOGGING['handlers']['console']['level'] = 'ERROR'

RESULTS_PATH_V1 = os.path.join(MEDIA_ROOT, 'results', 'testing', 'v1', '')
RESULTS_PATH = os.path.join(MEDIA_ROOT, 'results', 'testing', 'v3', '')
RESULTS_URL = MEDIA_URL + "results/testing/v3/"
RESULTS_URL_V1 = MEDIA_URL + "results/testing/v1/"