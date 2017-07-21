from base import *

# Ensure test runner does not create a test database for the admin user's credential set
if DATABASES and DATABASES.has_key('admin'):
	del DATABASES['admin']