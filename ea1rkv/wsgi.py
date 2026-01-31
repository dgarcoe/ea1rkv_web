"""WSGI config for EA1RKV Radioclub website."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ea1rkv.settings.dev")

application = get_wsgi_application()
