"""
Django settings for temmpo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
import os
import random
import string
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Dynamic config based on server host, vebuild and if dev, user name
SERVER = os.uname()[1]
THIS_PATH = os.path.dirname(__file__)
PROJECT_ROOT = '/'.join(THIS_PATH.split('/')[0:-6])

GENE_FILE_LOCATION = BASE_DIR + "/prepopulate/Homo_sapiens.gene_info"

ADMINS = (('Tessa Alexander', 'tessa.alexander+temmpo@bristol.ac.uk'),)

# SECURITY WARNING: keep the secret key used in production secret!
# Based on idea
# https://gist.github.com/ndarville/3452907

SECRET_FILE = os.path.join(THIS_PATH, 'secret.txt')
try:
    SECRET_KEY = open(SECRET_FILE).read().strip()
except IOError:
    try:
        SECRET_KEY = ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(50)])
        with open(SECRET_FILE, 'w') as secret_file:
            secret_file.write(SECRET_KEY)
    except IOError:
        raise Exception('Please create a file %s  with a secret key value.  See https://docs.djangoproject.com/en/1.8/ref/settings/#secret-key for more information.' % SECRET_FILE)

# SECURITY WARNING: don't run with debug turned on in production!  See prod.py settings file to change this value.
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1',
                 'localhost',
                 '.bris.ac.uk',
                 '.bristol.ac.uk',
                 'temmpo.org.uk',
                 'www.temmpo.org.uk', ]

# Application definition

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = ['registration', 'mptt', 'simple_autocomplete',]
LOCAL_APPS = ['browser', ]

INSTALLED_APPS = LOCAL_APPS + DEFAULT_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'temmpo.urls'

WSGI_APPLICATION = 'temmpo.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_L10N = False

USE_TZ = True

SHORT_DATE_FORMAT = 'd/m/Y'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
MEDIA_ROOT = "%s/var" % PROJECT_ROOT
STATIC_ROOT = "%s/var/www/static" % PROJECT_ROOT  # e.g. /usr/local/projects/temmpo/var/www/static

RESULTS_PATH = os.path.join(MEDIA_ROOT, 'results', '')

LOGIN_REDIRECT_URL = 'results_listing'  # 'search'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGOUT_REDIRECT_URL = 'login'

# Registration
ACCOUNT_ACTIVATION_DAYS = 14
REGISTRATION_AUTO_LOGIN = True
REGISTRATION_OPEN = True

#  Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)-8s %(process)d %(thread)d %(name)s:%(message)s',
            'datefmt': '%Y-%m-%d %a %H:%M:%S'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'local_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '%s/var/log/django.log' % PROJECT_ROOT,
            'maxBytes': 1024 * 1024 * 10,
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins', 'console', 'local_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'local_file'],
        'level': 'DEBUG',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True

SIMPLE_AUTOCOMPLETE = {'browser.meshterm': {'search_field': 'term', 'max_items': 10}}

# Import private settings specific to this environment like Database connections and SECRET_KEY
# from outside of public git repo.
try:
    from temmpo.settings.private_settings import *
except ImportError:
    print("No private settings where found in the expected location /usr/local/projects/temmpo/.settings/private_settings.py or symlinked into the temmpo/temmpo/settings/ directory")
