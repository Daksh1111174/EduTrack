import os
from pathlib import Path

from dotenv import load_dotenv
import dj_database_url


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

# Load .env when running locally.
# On Render, environment variables are provided by Render itself.
load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-student360-development-key"
)

DEBUG = os.environ.get(
    "DEBUG",
    "True"
).lower() in ("true", "1", "yes")


# Hosts allowed to access the Django application.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "corsheaders",
    "drf_spectacular",

    # EduTrack applications
    "accounts",
    "students",
    "teachers",
    "academics",
    "attendance",
    "behaviour",
    "assignments",
    "participation",
    "achievements",
    "remarks",
    "performance",
    "awards",
    "analytics",
    "reports",
    "notifications",
    "audit",
    "meetings",
    "gamification",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # Serve static files in production
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "student360.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

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


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "student360.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

# Local development:
#     SQLite
#
# Render production:
#     PostgreSQL through DATABASE_URL
#
# This allows the same settings.py to work in both environments.

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ============================================================
# CUSTOM USER MODEL
# ============================================================

AUTH_USER_MODEL = "accounts.User"


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.environ.get(
    "TIME_ZONE",
    "Asia/Kolkata"
)

USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# WhiteNoise static file configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND":
        "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],

    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination.PageNumberPagination",

    "PAGE_SIZE": 20,

    "DEFAULT_SCHEMA_CLASS":
        "drf_spectacular.openapi.AutoSchema",
}


# ============================================================
# DRF SPECTACULAR / API DOCUMENTATION
# ============================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "EduTrack Performance Analysis API",

    "DESCRIPTION": (
        "REST API for EduTrack Student Performance "
        "Analysis and Management Platform."
    ),

    "VERSION": "1.0.0",

    "SERVE_INCLUDE_SCHEMA": False,
}


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_URL = "login"

LOGIN_REDIRECT_URL = "dashboard"

LOGOUT_REDIRECT_URL = "login"


# ============================================================
# CORS
# ============================================================

# Development:
#     Allow all origins.
#
# Production:
#     Set CORS_ALLOWED_ORIGINS in Render.
#
# Example:
#
# CORS_ALLOWED_ORIGINS=https://edutrack-frontend.onrender.com

if DEBUG:

    CORS_ALLOW_ALL_ORIGINS = True

else:

    CORS_ALLOW_ALL_ORIGINS = False

    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ALLOWED_ORIGINS",
            ""
        ).split(",")
        if origin.strip()
    ]


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",")
    if origin.strip()
]


# ============================================================
# SECURITY SETTINGS
# ============================================================

if not DEBUG:

    # Redirect HTTP → HTTPS
    SECURE_SSL_REDIRECT = True

    # Secure cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Prevent browsers from MIME-sniffing responses
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Prevent clickjacking
    X_FRAME_OPTIONS = "DENY"

    # HTTP Strict Transport Security
    SECURE_HSTS_SECONDS = int(
        os.environ.get(
            "SECURE_HSTS_SECONDS",
            "31536000"
        )
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = False


# ============================================================
# SESSION SECURITY
# ============================================================

if not DEBUG:

    SESSION_COOKIE_HTTPONLY = True

    CSRF_COOKIE_HTTPONLY = False

    SESSION_COOKIE_SAMESITE = "Lax"

    CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# FILE UPLOAD LIMITS
# ============================================================

# 10 MB maximum upload size.
# Adjust if EduTrack needs larger certificates/documents.

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024


# ============================================================
# PROXY / HTTPS CONFIGURATION
# ============================================================

# Render sits behind a reverse proxy.
# This allows Django to correctly understand HTTPS requests.

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# PRODUCTION HOST SUPPORT
# ============================================================

# Render provides RENDER_EXTERNAL_HOSTNAME automatically.
# Add it to ALLOWED_HOSTS if available.

RENDER_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME"
)

if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    "version": 1,

    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format":
                "{levelname} {asctime} {module} "
                "{process:d} {thread:d} {message}",
            "style": "{",
        },

        "simple": {
            "format":
                "{levelname} {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },

    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get(
                "DJANGO_LOG_LEVEL",
                "INFO"
            ),
            "propagate": False,
        },
    },
}