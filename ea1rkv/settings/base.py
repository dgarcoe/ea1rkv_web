"""
Base Django settings for EA1RKV Radioclub website.

Common settings shared between development and production environments.
Environment-specific settings should go in dev.py or production.py.
"""

import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _

# --- Path Configuration ---

PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_DIR.parent

# --- Application Definition ---

INSTALLED_APPS = [
    # Wagtail apps
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "wagtail.contrib.search_promotions",
    "wagtail.contrib.settings",
    "wagtail.contrib.routable_page",
    # Third-party apps
    "modelcluster",
    "taggit",
    "widget_tweaks",
    "tinymce",
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Project apps
    "ea1rkv.apps.base",
    "ea1rkv.apps.home",
    "ea1rkv.apps.club",
    "ea1rkv.apps.blog",
    "ea1rkv.apps.events",
    "ea1rkv.apps.gallery",
    "ea1rkv.apps.members",
    "ea1rkv.apps.contact",
    "ea1rkv.apps.search",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "ea1rkv.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "ea1rkv.wsgi.application"

# --- Database ---

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "ea1rkv"),
        "USER": os.environ.get("POSTGRES_USER", "ea1rkv"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "ea1rkv"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# --- Authentication ---

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---

LANGUAGE_CODE = "es"

LANGUAGES = [
    ("es", _("Spanish")),
    ("gl", _("Galician")),
    ("en", _("English")),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --- Static & Media Files ---

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [PROJECT_DIR / "static"]

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# --- Wagtail Settings ---

WAGTAIL_SITE_NAME = "EA1RKV - Vigo Val Miñor Radioclub"

WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "http://localhost:8000")

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

WAGTAIL_I18N_ENABLED = True

WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

WAGTAILIMAGES_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

WAGTAILADMIN_COMMENTS_ENABLED = True

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    "default": {"WIDGET": "ea1rkv.apps.base.editors.ClassicRichTextWidget"},
}

# --- Default Primary Key ---

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Email ---

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "ea1rkv@example.com")

# --- Security ---

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
