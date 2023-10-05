"""
Django settings for temmpo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
import os
import random
import string
import sys

USING_APACHE = False

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Dynamic config based on server host, vebuild and if dev, user name
THIS_PATH = os.path.dirname(__file__)
PROJECT_ROOT = '/'.join(THIS_PATH.split('/')[0:-6])

GENE_FILE_LOCATION = BASE_DIR + "/prepopulate/Homo_sapiens.gene_info"

ADMINS = (('TeMMPo research project developers', 'it-temmpo-developers@bristol.ac.uk'),)

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
        raise Exception('Please create a file %s  with a secret key value.  See https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key for more information.' % SECRET_FILE)

# SECURITY WARNING: don't run with debug turned on in production!  See prod.py settings file to change this value.
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1',
                 'localhost',
                 '.bris.ac.uk',
                 '.bristol.ac.uk',
                 '.temmpo.org.uk',
                 'www.temmpo.org.uk', ]

# Application definition

DEFAULT_APPS = [
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.contenttypes', # Moved above to fix testing issue: https://code.djangoproject.com/ticket/9207
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = ['registration', 'mptt', 'django_rq', 'django_clamd', 'hcaptcha_field']
LOCAL_APPS = ['browser', 'dal', 'dal_select2',] # 'dal','dal_select2' are third party apps that need to be installed before 'django.contrib.admin'

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_L10N = False

USE_TZ = True

SHORT_DATE_FORMAT = 'd/m/Y'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
MEDIA_ROOT = "%s/var" % PROJECT_ROOT
STATIC_ROOT = "%s/var/www/static" % PROJECT_ROOT  # e.g. /usr/local/projects/temmpo/var/www/static

ORIGINAL_RESULTS_PATH = os.path.join(MEDIA_ROOT, 'results', '')
RESULTS_PATH_V1 = os.path.join(MEDIA_ROOT, 'results', 'v1', '')
RESULTS_PATH_V3 = os.path.join(MEDIA_ROOT, 'results', 'v3', '')
RESULTS_PATH_V4 = os.path.join(MEDIA_ROOT, 'results', 'v4', '')
RESULTS_PATH = RESULTS_PATH_V4

RESULTS_URL_V1 = MEDIA_URL + "results/v1/"
RESULTS_URL_V3 = MEDIA_URL + "results/v3/"
RESULTS_URL = MEDIA_URL + "results/v4/"

LOGIN_REDIRECT_URL = 'results_listing'
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
    'disable_existing_loggers': False,
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
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'local_file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'verbose',
            'filename': '%s/var/log/django.log' % PROJECT_ROOT,
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['mail_admins', 'console', 'local_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
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
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request'
            ],
        },
    },
]

X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True

# Number of days of inactivity before warning of deletion
# Gives 60 days of grace before deletion
ACCOUNT_CLOSURE_WARNING = 305

DEFAULT_FROM_EMAIL = 'TeMMPo <it-temmpo-developers@bristol.ac.uk>'

SITE_ID = 1

# Remove option to use in memory upload handler to allow for extraction via the file system and in future scanning before extraction.
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

RQ_QUEUES = {
    'default': {
        'HOST': '127.0.0.1',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360000,
    },
}

FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o775
FILE_UPLOAD_PERMISSIONS = 0o664
FILE_UPLOAD_TEMP_DIR = "%s/tmp" % MEDIA_ROOT

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'DB': 1,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        },
    },
}

CLAMD_SOCKET = '/var/run/clamd.scan/clamd.sock'
CLAMD_USE_TCP = False
CLAMD_TCP_SOCKET = 3310
CLAMD_TCP_ADDR = '127.0.0.1'
CLAMD_ENABLED = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

REGISTRATION_FORM = 'browser.forms.RegistrationCaptchaForm'

DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['MYSQL_DATABASE'],
        'USER': os.environ.get('MYSQL_USER', 'root'), # Development environment uses root - to ease creation of test DB in docker, env variable is set elsewhere for real DB username name
        'PASSWORD': os.environ['MYSQL_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        },
        'TEST': {
            'NAME': os.environ['TEST_DB_NAME'],
        },
    },
    'admin': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['MYSQL_DATABASE'],
        'USER': os.environ['MYSQL_ADMIN_USER'],
        'PASSWORD': os.environ['MYSQL_ADMIN_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    },
}

#DEV ONLY ref https://docs.hcaptcha.com/#integration-testing-test-keys
HCAPTCHA_SITEKEY = os.environ.get('HCAPTCHA_SITEKEY', '')
HCAPTCHA_SECRET = os.environ.get('HCAPTCHA_SECRET', '')
