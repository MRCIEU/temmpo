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