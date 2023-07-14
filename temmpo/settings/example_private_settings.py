"""Example private settings file.

Each build needs to define their own copy which should be located in /usr/local/projects/temmpo/.settings.private_settings.py

NB: The SQLite database entry is for legacy purposes.  The admin entry should point to the same database but also as mysql
but have a user account with additional grants, e.g. at least DROP/CREATE TABLE/DATABASE level permissions.
"""

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
    'admin': {
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
}

DATABASES['default'] = DATABASES['mysql']

#DEV ONLY ref https://docs.hcaptcha.com/#integration-testing-test-keys
HCAPTCHA_SITEKEY = '10000000-ffff-ffff-ffff-000000000001'
HCAPTCHA_SECRET = '0x0000000000000000000000000000000000000000'