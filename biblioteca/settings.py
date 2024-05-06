"""
Django settings for biblioteca project.

Generated by 'django-admin startproject' using Django 5.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from os import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(environ.get("DEBUG", 1)))

ALLOWED_HOSTS = ["*"] if DEBUG else environ.get("ALLOWED_HOSTS", "").split()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = (
    "django-insecure-(j=u)7ztio@ljv%l)wim0be#awn_4(j%i#bps8(_s@*z3es*2g"
    if DEBUG
    else environ.get("SECRET_KEY", "localhost")
)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = (
    "django-insecure-(j=u)7ztio@ljv%l)wim0be#awn_4(j%i#bps8(_s@*z3es*2g"
)


CSRF_TRUSTED_ORIGINS = environ.get("CSRF_TRUSTED_ORIGINS", "").split()
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG


# Application definition

INSTALLED_APPS = [
    "public_admin",
    "biblioteca.apps.BibliotecaAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "fieldsets_with_inlines",
    "solo",
    "adminsortable2",
    "profiles",
    "books",
    "loans",
    "barcodes",
    "dynamic_admin_site",
    "admin_buttons",
    "site_configuration",
    "tinymce",
    "django_object_actions",
    "notifications",
    "colorfield",
] + (
    [
        "django_extensions",
        "debug_toolbar",
    ]
    if DEBUG
    else []
)


MIDDLEWARE = [
    *(["debug_toolbar.middleware.DebugToolbarMiddleware"] if DEBUG else []),
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "biblioteca.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "biblioteca.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": environ.get("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": environ.get("SQL_USER", "user"),
        "PASSWORD": environ.get("SQL_PASSWORD", "password"),
        "HOST": environ.get("SQL_HOST", "localhost"),
        "PORT": environ.get("SQL_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = "static/"
MEDIA_URL = "media/"

STATIC_ROOT = Path(environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "static/"))
MEDIA_ROOT = Path(environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media/"))

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TINYMCE_JS_URL = (
    "https://cdnjs.cloudflare.com/ajax/libs/tinymce/7.0.1/tinymce.min.js"
)

INTERNAL_IPS = ["127.0.0.1"] if DEBUG else []

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "notifications.mail.DynamicSMPTEmailBackend"
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
}
