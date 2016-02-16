"""
Django settings for x project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import socket
import sys

from unipath import Path

DEVELOPER_HOSTS = ['mac2-2.local']
BASE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
GIT_DIR = BASE_DIR.ancestor(1)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')-8xsg3omyyv^jbm5tp=p%!l#)!br+c+6k4e9$(4c3h+&anel+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'edc_crypto_fields',
    # 'apps.bcpp_subject',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'bcpp_export.urls'

WSGI_APPLICATION = 'bcpp_export.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

if 'test' in sys.argv and socket.gethostname() in DEVELOPER_HOSTS:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
# elif 'test' in sys.argv:
#     DATABASES = TRAVIS_MYSQL
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'OPTIONS': {
                'init_command': 'SET storage_engine=INNODB',
            },
            'NAME': 'bhp066_master',
            'USER': 'root',
            'PASSWORD': 'cc3721b',
            'HOST': '127.0.0.1',
            'PORT': '10000',
            'ATOMIC_REQUESTS': True,
        },
    }

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

SERVER_DEVICE_ID_LIST = ['99']
MIDDLEMAN_DEVICE_ID_LIST = []
PROJECT_ROOT = BASE_DIR.ancestor(1)
FIELD_MAX_LENGTH = 'default'
IS_SECURE_DEVICE = True
KEY_PATH = '/Volumes/bhp066/live_keys'  # BASE_DIR.ancestor(1)
KEY_PREFIX = 'user'
ALLOW_MODEL_SERIALIZATION = True
MAX_SUBJECTS = 0

ADMIN_EXCLUDE_DEFAULT_CODE = 'T0'
CURRENT_COMMUNITY = 'bhp'
CURRENT_COMMUNITY_CHECK = False
CURRENT_MAPPER = CURRENT_COMMUNITY
CURRENT_SURVEY = 'bcpp-year-1'
DEVICE_ID = '99'
GPS_DEVICE = '/Volumes/GARMIN/'
GPS_FILE_NAME = '/Volumes/GARMIN/GPX/temp.gpx'
GPX_TEMPLATE = None
SITE_CODE = '00'
VERIFY_GPS = False
VERIFY_GPS_LOCATION = False
VERIFY_PLOT_COMMUNITY_WITH_CURRENT_MAPPER = False
LIMIT_EDIT_TO_CURRENT_COMMUNITY = False
