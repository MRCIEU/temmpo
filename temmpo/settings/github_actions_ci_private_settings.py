DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ci',
        'USER': 'root',
        'PASSWORD': 'ci-db-pswd',
        'HOST': '127.0.0.1',
        'PORT': '',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    }
}

# redis available over localhost, may need to redefine if any issues

# clamd testing is enabled specifically for selenium tests or Apache fronted VMs.
CLAMD_ENABLED = False