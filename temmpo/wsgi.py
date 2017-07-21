#!/usr/local/projects/tmma/lib/prod/bin/python
"""
WSGI config for temmpo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
sys.path.insert(0, PROJECT_ROOT)

HOSTS_ENV = {'localhost.localdomain': 'dev',
             'py-web-t0.epi': 'test',
             'py-web-d0.epi': 'demo',
             'py-web-p0.epi': 'prod'}

ENV = HOSTS_ENV.get(os.uname()[1], 'dev')
os.environ["DJANGO_SETTINGS_MODULE"] = "temmpo.settings." + ENV

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
