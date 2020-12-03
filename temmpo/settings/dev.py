from base import *

import os

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK' : lambda request: True,
    'INTERCEPT_REDIRECTS': False,
}

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'pympler.panels.MemoryPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    # 'debug_toolbar.panels.cache.CachePanel',
    # 'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    # 'debug_toolbar.panels.redirects.RedirectsPanel',
]

DEV_APPS = ['debug_toolbar', 'pympler', ]
INSTALLED_APPS.extend(DEV_APPS)

DEV_MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
MIDDLEWARE.extend(DEV_MIDDLEWARE)

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/usr/local/projects/temmpo/var/email'

LOGGING['handlers']['console']['level'] = 'DEBUG'

USING_APACHE = (os.environ.has_key("USING_APACHE") and os.environ["USING_APACHE"] == 'True')

# # Disable ClamAV for Django development runner
# if not USING_APACHE:
#     CLAMD_ENABLED = False