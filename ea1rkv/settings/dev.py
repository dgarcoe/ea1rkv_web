"""
Development settings for EA1RKV Radioclub website.

These settings are NOT suitable for production.
See production.py for production configuration.
"""

import os
from pathlib import Path

from .base import *  # noqa: F401, F403

DEBUG = True

SECRET_KEY = "django-insecure-dev-only-ea1rkv-change-me-in-production"

ALLOWED_HOSTS = ["*"]

# --- Database ---
# Use SQLite by default for development (works in Codespaces without Docker).
# Set USE_POSTGRES=1 to use PostgreSQL instead (e.g. in docker-compose).

if os.environ.get("USE_POSTGRES"):
    pass  # Keep the PostgreSQL config from base.py
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(BASE_DIR) / "db.sqlite3",  # noqa: F405
        }
    }

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
