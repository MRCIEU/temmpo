DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pipelines',
        'USER': 'test_user',
        'PASSWORD': 'test_user_password',
        'HOST': '0.0.0.0',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    }
}
