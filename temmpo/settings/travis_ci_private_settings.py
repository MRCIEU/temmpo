DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'travis',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    }
}

# redis available over localhost, may need to redefine if any issues

# clamd testing is enabled for VM based Jenkins run tests.
CLAMD_ENABLED = False