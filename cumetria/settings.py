"""
Django settings for Cumetria.

Everything that differs between your PC and the server comes from environment
variables (see .env.example). Nothing secret is stored in this file.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    """Read a true/false environment variable ("true", "1", "yes" count as true)."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Read a comma-separated environment variable into a list."""
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# --- Core -------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "insecure-local-development-key"
    else:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY (see .env.example).")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "cumetria.urls"
WSGI_APPLICATION = "cumetria.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.theme",
            ],
        },
    },
]

# --- Data -------------------------------------------------------------------

# One folder holds everything that must be backed up: the database and uploads.
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            # WAL lets people read while someone else writes; busy_timeout waits
            # briefly instead of failing when two writes happen at the same moment.
            "init_command": (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA synchronous=NORMAL;"
                "PRAGMA busy_timeout=5000;"
                "PRAGMA foreign_keys=ON;"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_ROOT = DATA_DIR / "media"
MEDIA_URL = "/media/"

# --- Languages and time ------------------------------------------------------

LANGUAGE_CODE = "ro"
LANGUAGES = [
    ("ro", _("Romanian")),
    ("en", _("English")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True

TIME_ZONE = "Europe/Bucharest"
USE_TZ = True

# --- Static files -------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# While developing, serve files straight from static/ (no collectstatic needed).
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# --- Security ----------------------------------------------------------------

# Caddy sits in front of Django and handles HTTPS; it tells Django the original
# request was HTTPS through this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# On the real server (HTTPS) cookies are only sent over encrypted connections.
# Locally over plain http this must be false, or logging in would not work.
USE_HTTPS = env_bool("DJANGO_HTTPS", default=False)
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
LANGUAGE_COOKIE_SECURE = USE_HTTPS
# Tell browsers to always use HTTPS for this site. Starts at one day; can be
# raised once the domain and certificates have run smoothly for a while.
SECURE_HSTS_SECONDS = 60 * 60 * 24 if USE_HTTPS else 0
# W008: Caddy already redirects http:// to https://, so Django doesn't need to.
# W005/W021: HSTS for subdomains and browser preload lists stay off; the domain
# may be a free subdomain shared with others, where those would be wrong.
SILENCED_SYSTEM_CHECKS = ["security.W008", "security.W005", "security.W021"]
SESSION_COOKIE_AGE = 60 * 60 * 24 * 90  # stay logged in for 90 days
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

AUTH_PASSWORD_VALIDATORS = []  # nobody uses passwords: Google or email-link login only

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
