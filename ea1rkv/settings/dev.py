"""
Development settings for EA1RKV Radioclub website.

These settings are NOT suitable for production.
See production.py for production configuration.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

SECRET_KEY = "django-insecure-dev-only-ea1rkv-change-me-in-production"

ALLOWED_HOSTS = ["*"]

# --- Email ---

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# --- Caching ---

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# --- Debug Toolbar (optional) ---

try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1", "::1"]
except ImportError:
    pass

# --- Wagtail ---

WAGTAILADMIN_BASE_URL = "http://localhost:8000"
