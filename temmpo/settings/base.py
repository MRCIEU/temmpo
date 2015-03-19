"""
Django settings for temmpo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'fva(zwxn6)g6bk$46e=(_b-5&*y1%!jd*hrn+yke91g@i#%dj%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

APACHE = False

# Application definition

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = ['registration', 'mptt', ] # 'oraclepool',
LOCAL_APPS = ['browser',]

INSTALLED_APPS = DEFAULT_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'temmpo.urls'

WSGI_APPLICATION = 'temmpo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_L10N = False

USE_TZ = True

SHORT_DATE_FORMAT = 'd/m/Y'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
MEDIA_ROOT = VAR_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', '..','..','var'))

LOGIN_REDIRECT_URL = 'results-listing' # 'search'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

# Registration
ACCOUNT_ACTIVATION_DAYS = 14
REGISTRATION_AUTO_LOGIN = True
REGISTRATION_OPEN = True

# Import private settings specific to this environment like Database connections and SECRET_KEY
# from outside of public git repo.

# settings_file_name = 'temmpo_private_settings.py'
# paths = (os.path.join(os.path.expanduser("~"), settings_file_name), 
#     os.path.normpath(os.path.join(BASE_DIR, '..', '..','..','etc', settings_file_name)))

# for path in paths:
#     if os.path.exists(path):
#         execfile(path)
#         break
# else:
#     print("Warning: Expected to find a local private settings override file in one of these locations")
#     print(paths)
