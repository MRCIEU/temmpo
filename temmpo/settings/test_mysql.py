"""Test specific settings file, currently used for Vagrant test suites."""

from base import *

if DATABASES:

    # Ensure test runner does not create a test database for the admin user's credential set
    if 'admin' in DATABASES:
        del DATABASES['admin']

    # Ensure test runner does not create a test database for the legacy SQLite DB config
    if 'sqlite' in DATABASES:
        del DATABASES['sqlite']

RQ_QUEUES['default']['ASYNC'] = False

LOGGING['handlers']['console']['level'] = 'ERROR'

RESULTS_PATH_V4 = os.path.join(MEDIA_ROOT, 'results', 'testing', 'v4', '')
RESULTS_PATH_V3 = os.path.join(MEDIA_ROOT, 'results', 'testing', 'v3', '')
RESULTS_PATH_V1 = os.path.join(MEDIA_ROOT, 'results', 'testing', 'v1', '')
RESULTS_PATH = RESULTS_PATH_V4
RESULTS_URL = MEDIA_URL + "results/testing/v4/"
RESULTS_URL_V3 = MEDIA_URL + "results/testing/v3/"
RESULTS_URL_V1 = MEDIA_URL + "results/testing/v1/"

CLAMD_ENABLED = False