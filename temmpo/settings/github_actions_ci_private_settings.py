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

DATABASES['admin'] = DATABASES['default']

# redis available over localhost, may need to redefine if any issues

# clamd testing is enabled specifically for selenium tests or Apache fronted VMs.
CLAMD_ENABLED = False

#DEV ONLY ref https://docs.hcaptcha.com/#integration-testing-test-keys
HCAPTCHA_SITEKEY = '10000000-ffff-ffff-ffff-000000000001'
HCAPTCHA_SECRET = '0x0000000000000000000000000000000000000000'