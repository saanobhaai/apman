"""
Django settings for apman project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('APMAN_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('APMAN_DEBUG', False)
USE_S3 = os.getenv('APMAN_USE_S3', True)
SESSION_COOKIE_SECURE = os.getenv('APMAN_SESSION_COOKIE_SECURE', True)
CSRF_COOKIE_SECURE = os.getenv('APMAN_CSRF_COOKIE_SECURE', True)
ALLOWED_HOSTS = os.getenv('APMAN_ALLOWED_HOSTS').split(',')
ADMINS = [('Sonic Planetarium Support', os.getenv('APMAN_EMAIL_HOST_USER')), ]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Application definition

INSTALLED_APPS = [
    'satsound.apps.SatsoundConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_extensions',
    'rest_framework',
    'storages',
    'django_cleanup',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'apman.urls'

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

WSGI_APPLICATION = 'apman.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('APMAN_MYSQL_NAME'),
        'USER': os.getenv('APMAN_MYSQL_USER'),
        'PASSWORD': os.getenv('APMAN_MYSQL_PASSWORD'),
        'HOST': os.getenv('APMAN_MYSQL_HOST'),
        'PORT': os.getenv('APMAN_MYSQL_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'audio/')
MEDIA_URL = '/audio/'

AWS_ACCESS_KEY_ID = os.getenv('APMAN_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('APMAN_AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('APMAN_STORAGE_BUCKET_NAME')
AWS_QUERYSTRING_AUTH = False
S3_URL = 'https://s3.amazonaws.com/%s/' % AWS_STORAGE_BUCKET_NAME

if USE_S3:
    DEFAULT_FILE_STORAGE = 'apman.s3utils.MediaRootS3BotoStorage'
    MEDIA_URL = '%s%s' % (S3_URL, 'media/')

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

SPACETRACK_IDENTITY = os.getenv('APMAN_SPACETRACK_IDENTITY')
SPACETRACK_PASSWORD = os.getenv('APMAN_SPACETRACK_PASSWORD')

AUDIO_TYPES = (
    'audio/aac',  # .aac
    'audio/basic',  # .au .snd
    'audio/mpeg',  # .mp1 .mp2 .mp3 .mpg .mpeg
    'audio/mp4',  # .mp4 .m4a
    'audio/vnd.wav',  # .wav
    'audio/wav',  # .wav
    'audio/wave',  # .wav
    'audio/x-wav',  # .wav
    'audio/x-pn-wav',  # .wav
    'audio/x-aiff',  # .aif .aifc .aiff
    'audio/flac',
)
MAX_AUDIOFILE_SIZE = 30 * 1024 * 1024  # mb

MAX_IMMINENCE = 1  # number of hours to consider 'recent' when comparing audio timestamps to trajectory rise times
TRAJECTORY_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_TIMEZONE = 'Europe/London'

CSRF_TRUSTED_ORIGINS = (
    '.sonicplanetarium.net',
)

# Email configuration.

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('APMAN_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('APMAN_EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv('APMAN_EMAIL_HOST_USER')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # mandatory, none
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'commands_logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/ap/log/commands.log',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
        },
        'commands': {
            'handlers': ['commands_logfile', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}
