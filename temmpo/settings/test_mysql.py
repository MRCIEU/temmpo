from base import *

if DATABASES:

	# Ensure test runner does not create a test database for the admin user's credential set
	if DATABASES.has_key('admin'):
		del DATABASES['admin']

	# Ensure test runner does not create a test database for the legacy sqlite db
	if DATABASES.has_key('sqlite'):
		del DATABASES['sqlite']

