#!/usr/local/projects/tmma/lib/dev/bin/python
"""
WSGI config for temmpo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "temmpo.settings.dev"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
sys.path.insert(0, PROJECT_ROOT)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
