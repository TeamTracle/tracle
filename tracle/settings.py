import os

from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

DEBUG = os.environ.get('DEBUG', '1') == '1'
SECRET_KEY = os.environ.get('SECRET_KEY', 'SECRETDEVKEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1;localhost').split(';')
ROOT_URLCONF = 'tracle.urls'
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('SQL_DATABASE', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.environ.get('SQL_USER', 'user'),
        'PASSWORD': os.environ.get('SQL_PASSWORD', 'password'),
        'HOST': os.environ.get('SQL_HOST', 'localhost'),
        'PORT': os.environ.get('SQL_PORT', '5432'),
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'backend.apps.BackendConfig',
    'web.apps.WebConfig',
    'api.apps.ApiConfig',

    'django_rq',
    'video_encoding',
] 

DEV_APPS = os.environ.get('INSTALLED_APPS', None) 
if DEV_APPS:
    INSTALLED_APPS += DEV_APPS.split(';')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG and 'debug_toolbar' in INSTALLED_APPS:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tracle.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.AllowAllUsersModelBackend',
)
AUTH_USER_MODEL = 'backend.User'

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', os.path.join(BASE_DIR, 'static'))

# for dev toolbar

# for video_encoding
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 3600,
    },
}

VIDEO_ENCODING_BACKEND = 'video_encoding.backends.ffmpeg.FFmpegBackend'
VIDEO_ENCODING_THREADS = 1
VIDEO_ENCODING_PROGRESS_UPDATE = 30
VIDEO_ENCODING_BACKEND_PARAMS = {}
VIDEO_ENCODING_FORMATS = {
    'FFmpeg': [
        {
            'name': 'mp4_sd',
            'extension': 'mp4',
            'params': [
                '-codec:v', 'libx264', '-crf', '20', '-preset', 'medium',
                '-b:v', '1000k', '-maxrate', '1000k', '-bufsize', '2000k',
                '-vf', 'scale=-2:480',  # http://superuser.com/a/776254
                '-codec:a', 'aac', '-b:a', '128k', '-strict', '-2',
            ],
        },
        {
            'name': 'mp4_hd',
            'extension': 'mp4',
            'params': [
                '-codec:v', 'libx264', '-crf', '20', '-preset', 'medium',
                '-b:v', '3000k', '-maxrate', '3000k', '-bufsize', '6000k',
                '-vf', 'scale=-2:720',
                '-codec:a', 'aac', '-b:a', '128k', '-strict', '-2',
            ],
        },
    ]
}

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
MEDIA_URL = '/media/'
TRACLE_UPLOAD_PATH = os.environ.get('UPLOAD_PATH', os.path.join(BASE_DIR, 'uploads'))
FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.TemporaryFileUploadHandler']

CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', 'localhost')
DOMAIN = os.environ.get('DOMAIN', 'localhost')

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'noreply@example.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'PASSWORD')
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.example.com')
EMAIL_PORT = 587
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

LOGGING = {
    'version' : 1,
    'disable_existing_loggers' : False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters' : {
        'require_debug_true' : {
            '()' : 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers' : {
        'console' : {
            'class' : 'logging.StreamHandler',
            'formatter' : 'simple',
            'filters' : ['require_debug_true'],
        },
        'file' : {
            'level' : os.environ.get('LOGLEVEL', 'WARNING'),
            'class' : 'logging.FileHandler',
            'filename' : os.path.join(BASE_DIR, 'tracle.log'),
            'formatter' : 'verbose', 
        },
    },
    'loggers' : {
        'django' : {
            'handlers' : ['console', 'file'],
            'level' : os.environ.get('LOGLEVEL', 'WARNING'),
            'propagate' : True,
        },
    },
}