import os
import sys

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

DEBUG = os.environ.get("DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY", "SECRETDEVKEY")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1;localhost").split(";")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "1") == "1"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") == "1"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "1") == "1"
CSRF_COOKIE_DOMAIN = os.environ.get("CSRF_COOKIE_DOMAIN", "localhost")
SECURE_BROWSER_XSS_FILTER = os.environ.get("SECURE_BROWSER_XSS_FILTER", "1") == "1"

CURRENT_SITE = {
    "name": os.environ.get("CURRENT_SITE_NAME", "localhost"),
    "domain": os.environ.get("CURRENT_SITE_DOMAIN", "localhost:8000"),
    "protocol": os.environ.get("CURRENT_SITE_PROTOCOL", "http"),
}

ROOT_URLCONF = "tracle.urls"


DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "qsessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.humanize",
    "backend.apps.BackendConfig",
    "web.apps.WebConfig",
    "api.apps.ApiConfig",
    "django_rq",
    "compressor",
    "rest_framework",
    "cacheops",
    "imagekit",
    "colorfield",
    "waffle",
    "actstream",
    "captcha",
]

DEV_APPS = os.environ.get("INSTALLED_APPS", None)
if DEV_APPS:
    INSTALLED_APPS += DEV_APPS.split(";")

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    "qsessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "web.middleware.SelectedChannelMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "waffle.middleware.WaffleMiddleware",
]

if "silk" in INSTALLED_APPS:
    MIDDLEWARE.append("silk.middleware.SilkyMiddleware")

SESSION_ENGINE = "qsessions.backends.db"

if DEBUG and "debug_toolbar" in INSTALLED_APPS:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "tracle.wsgi.application"

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTHENTICATION_BACKENDS = (
    "backend.auth_backends.AuthBackend",
    "django.contrib.auth.backends.AllowAllUsersModelBackend",
)
AUTH_USER_MODEL = "backend.User"

STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", os.path.join(BASE_DIR, "static"))
STATICFILES_STORAGE = "compressor.storage.CompressorFileStorage"
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
LIBSASS_OUTPUT_STYLE = "nested"
COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "django_compressor_autoprefixer.AutoprefixerFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}
COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_ENABLED = not DEBUG
COMPRESS_OFFLINE = not DEBUG


# for video_encoding
RQ_QUEUES = {
    "default": {
        "HOST": os.environ.get("REDIS_RQ_HOST", "localhost"),
        "PORT": int(os.environ.get("REDIS_RQ_PORT", "6379")),
        "DB": int(os.environ.get("REDIS_RQ_DB", "0")),
        "DEFAULT_TIMEOUT": int(os.environ.get("REDIS_RQ_DEFAULT_TIMEOUT", "3600")),
    },
}

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
MEDIA_URL = "/media/"
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.TemporaryFileUploadHandler"]

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "noreply@example.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "PASSWORD")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "mail@example.com")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "server",
            "stream": sys.stdout,
        },
    },
    "formatters": {
        "server": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOGLEVEL", "INFO"),
            "propagate": True,
        },
        "backend": {
            "handlers": ["console"],
            "level": os.environ.get("TRACLE_LOGLEVEL", "DEBUG"),
            "propagate": False,
        },
    },
}


BUNNYCDN = {
    "enabled": os.environ.get("BUNNYCDN_ENABLED", "0") == "1",
    "storage_zone_name": os.environ.get("BUNNYCDN_STORAGE_ZONE_NAME", None),
    "access_token": os.environ.get("BUNNYCDN_ACCESS_TOKEN", None),
    "pullzone_url": os.environ.get("BUNNYCDN_PULLZONE_URL", None),
    "account_token": os.environ.get("BUNNYCDN_ACCOUNT_TOKEN", None),
}

BUNNYNET = {
    "enabled": os.environ.get("BUNNYNET_ENABLED", "0") == "1",
    "access_token": os.environ.get("BUNNYNET_ACCESS_TOKEN", None),
    "library_id": os.environ.get("BUNNYNET_LIBRARY_ID", None),
    "storage_url": os.environ.get("BUNNYNET_STORAGE_URL", None),
    "callback_key": os.environ.get("BUNNYNET_CALLBACK_KEY", ""),
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

CACHEOPS_REDIS = {
    "host": os.environ.get("REDIS_CACHE_HOST", "localhost"),
    "port": int(os.environ.get("REDIS_CACHE_PORT", "6379")),
    "db": int(os.environ.get("REDIS_CACHE_DB", "1")),
}

CACHEOPS_DEFAULTS = {"timeout": 60 * 60}
CACHEOPS = {
    # 'backend.*': {'ops': {'get', 'fetch'}},
    "*.*": {},
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
        "TIMEOUT": 86400,
    }
}

ALLOW_VIDEO_UPLOAD = os.environ.get("ALLOW_VIDEO_UPLOAD", "0") == "1"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SILKY_META = True
SILKY_PYTHON_PROFILER = True
