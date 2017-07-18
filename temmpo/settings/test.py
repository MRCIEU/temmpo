from base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/usr/local/projects/temmpo/var/data/db.sqlite3',
    }
}

DATABASES['admin'] = DATABASES['default']
