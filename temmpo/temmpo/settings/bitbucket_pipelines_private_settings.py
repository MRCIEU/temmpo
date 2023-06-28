DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pipelines',
        'USER': 'root',
        'PASSWORD': 'Root_Testing_Password!',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    }
}

# clamd testing is enabled for VM based Jenkins run tests.
CLAMD_ENABLED = False
