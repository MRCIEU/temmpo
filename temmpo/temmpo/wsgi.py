"""
WSGI config for temmpo project.

It exposes the WSGI callable as a module-level variable named ``application``.
It deduces the settings file name based on the virtual directory name

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""
import os
import sys

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SRC_DIR)
vedir = SRC_DIR.split('/')[-3]
os.environ["DJANGO_SETTINGS_MODULE"] = "temmpo.settings.%s" % vedir

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
