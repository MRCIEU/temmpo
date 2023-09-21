# Based on similar probes created by Research IT

import time
import logging
import sys

from django.views.generic import TemplateView
from django.contrib import messages
# from django.conf import settings
from django.core import mail
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

class ProbeView(TemplateView):
    template_name = "probe.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        status = 200 if context['passed'] else 418
        return self.render_to_response(context, status=status)

    def get_context_data(self, **kwargs):
        start = time.time()

        context = super(ProbeView, self).get_context_data(**kwargs)
        components = []

        self.check(components, 'Database connection', self.probe_database)

        self.check(components, 'Database ORM', self.probe_orm)

        self.check(components, 'Email sending', self.probe_email)

        #self.check(components, 'Static file access', self.probe_staticfiles)

        self.check(components, 'Python version', self.python_version)

        context['components'] = components

        end = time.time()
        if [x for x in components if not x['pass'] and not x['allow_fail']]:
            context['passed'] = False
            messages.add_message(self.request, messages.WARNING, "FAIL")
        else:
            context['passed'] = True
            messages.add_message(self.request, messages.SUCCESS, "PASS")

        context['duration'] = "{0:.4f}".format(round(end - start, 4))

        return context

    def check(self, components, label='', function=None, max_duration=5, allow_fail=False):
        start = time.time()
        success = False
        try:
            success = function()
            end = time.time()
            if end - start > max_duration:
                logger.warn(
                    "Check timestamp exceeded for '%s' (%s took longer than %s)" % (label, end - start, max_duration))
        except Exception as e:
            end = time.time()
            logger.error("Problem with '%s' check: %s" % (label, e))

        components.append({'label': label,
                           'pass': success,
                           'allow_fail': allow_fail,
                           'time': "{0:.4f}".format(round(end - start, 4))})

    def probe_database(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM django_site LIMIT 1")
        result = cursor.fetchall()
        return result[0][0] == 1

    def probe_orm(self):
        from django.contrib.sites.models import Site
        return Site.objects.all().exists()


    def probe_email(self):
        email_con = mail.get_connection()
        email_con.open()
        try:
            send_mail(
                'Email subject',
                'This is the message body.',
                'blackhole@bristol.ac.uk',
                ['blackhole@bristol.ac.uk'],
                fail_silently=False,
            )
        except:
            email_con.close()
            return False
        else:
            email_con.close()
            return True

    def python_version(self):
        if sys.version_info.major == 3 and sys.version_info.minor == 8:
            return True
        else:
            return False

    # def probe_staticfiles(self):
    #     # GETTING FILE HANGS WITH SSL ERROR?
    #     import urllib.request
    #
    #     if settings.VEDIR not in ['demo', 'prod']:
    #         # Don't run in dev
    #         return True
    #
    #     url = settings.STATIC_URL + 'css/styles.css'
    #     url = self.request.build_absolute_uri(url)
    #
    #     with urllib.request.urlopen(url) as response:
    #         html = response.read()
    #         if 'menu-container' in html:
    #             return True
    #
    #     return False