# -*- coding: utf-8 -*-
"""
Django settings for dic-quo project.
"""

import environ
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Reading .env file
# BASE_DIR is .../dicquo/
# Project root (where .env is) is .../dicquo/../ or ../../ from settings.py
# If BASE_DIR is .../dicquo, then .env is at BASE_DIR.parent/.env
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

# Custom Admin URL from .env
ADMIN_URL = env('ADMIN_URL', default='admin/')

#########################################
# Настройки сообщений об ошибках когда все упало и т.п.
ADMINS = (('Admin', env('ADMIN_EMAIL', default='admin@example.com')),)

#########################################
# настройки для почтового сервера
EMAIL_CONFIG = env.email_url(
    'EMAIL_URL', default='smtp://user:password@localhost:25')
vars().update(EMAIL_CONFIG)

SERVER_EMAIL = DEFAULT_FROM_EMAIL = EMAIL_CONFIG['EMAIL_HOST_USER']
EMAIL_SUBJECT_PREFIX = '[DIC-QUO ERR]: '  # префикс для оповещений об ошибках и необработанных исключениях

# Application definition
INSTALLED_APPS: list[str] = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'taggit.apps.TaggitAppConfig',
    'web.apps.WebConfig',
]

MIDDLEWARE: list[str] = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF: str = 'dicquo.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent / 'database/db.sqlite3',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'dicquo.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = 'ru-RU'         # <--------- RUSSIAN
TIME_ZONE = 'Europe/Moscow'     #
USE_I18N = True
USE_L10N = True
USE_TZ = True               # учитывать часовой пояс
FIRST_DAY_OF_WEEK = 1       # неделя начинается с понедельника
# APPEND_SLASH = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Using pathlib for cleaner path management
# Adjusted to serve from public/media relative to project root
MEDIA_ROOT = BASE_DIR.parent / 'public/media'

# STATIC_ROOT is where collectstatic collects files for production.
# It cannot be the same as a directory in STATICFILES_DIRS.
STATIC_ROOT = BASE_DIR.parent / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR.parent / 'public/static',
]

# Enable WhiteNoise's Gzip compression of static assets.
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Конфигурация WhiteNoise для обслуживания статических файлов и файлов из /public (например, robots.txt, favicon.ico и т.п.)
WHITENOISE_ROOT = BASE_DIR.parent / 'public'

SITE_ID = 1
