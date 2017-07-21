DATABASES = {
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '##MISSING##',
        'USER': '##MISSING##',
        'PASSWORD': '##MISSING##',
        'HOST': '##MISSING##',
        'PORT': '##MISSING##',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    },
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/usr/local/projects/temmpo/var/data/db.sqlite3',
    }
}

DATABASES['default'] = DATABASES['sqlite']
DATABASES['admin'] = DATABASES['sqlite']
