"""
Django settings for openlxp_xss_project project.

Generated by 'django-admin startproject' using Django 3.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import mimetypes
import os
import sys
from pathlib import Path

from neomodel import config
config.DATABASE_URL = os.environ.get('NEO4J_BOLT_URL', 'bolt://neo4j:password@neo4j:7687')

IS_CCV = os.environ.get('IS_CCV', False)
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY_VAL')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

mimetypes.add_type("text/css", ".css", True)

ALLOWED_HOSTS = ['*']

# Application definition

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8010',  # Add the port if needed
    'http://127.0.0.1:8010',
]

INSTALLED_APPS = [
    "django_neomodel",
    "admin_interface",
    "colorfield",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'core.apps.CoreConfig',
    'api',
    'users',
    'social_django',
    'uid',
    'openlxp_authentication',
    'deconfliction_service',
    'ccv',
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

ROOT_URLCONF = 'openlxp_xss_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'openlxp_xss_project.wsgi.application'

## Encryption key for django-encrypted-model-fields

FIELD_ENCRYPTION_KEY = 'NzVkgiLCyzOePBWCKvUTc38M4YWiQjsD0zc9m7x_iLo='

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': 3306,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'loggers': {
        'dict_config_logger': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'simpleRe',
        },
    },

    'formatters': {
        'simpleRe': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        }
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'users.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'openlxp_authentication.models.SAMLDBAuth',
)

# openlxp_authentication settings openlxp_authentication documentation:
# https://github.com/OpenLXP/openlxp-authentication#readme
# social_django documentation:
# https://python-social-auth.readthedocs.io/en/latest/index.html
# SOCIAL_AUTH_STRATEGY = 'openlxp_authentication.models.SAMLDBStrategy'
JSONFIELD_ENABLED = True
USER_MODEL = 'users.CustomUser'
SESSION_EXPIRATION = True

if os.environ.get('LOGIN_REDIRECT_URL') is not None:
    LOGIN_REDIRECT_URL = os.environ.get('LOGIN_REDIRECT_URL')

if os.environ.get('OVERIDE_HOST') is not None:
    OVERIDE_HOST = os.environ.get('OVERIDE_HOST')
    BAD_HOST = os.environ.get('BAD_HOST')

if os.environ.get('STRATEGY') is not None:
    SOCIAL_AUTH_STRATEGY = os.environ.get('STRATEGY')

SP_ENTITY_ID = os.environ.get('ENTITY_ID')

SP_PUBLIC_CERT = os.environ.get('SP_PUBLIC_CERT')
SP_PRIVATE_KEY = os.environ.get('SP_PRIVATE_KEY')
ORG_INFO = {
    "en-US": {
        "name": "example",
        "displayname": "Example Inc.",
        "url": "http://localhost",
    }
}
TECHNICAL_CONTACT = {
    "givenName": "Tech Person",
    "emailAddress": "technical@localhost.com"
}
SUPPORT_CONTACT = {
    "givenName": "Support Person",
    "emailAddress": "support@localhost.com",
}
USER_ATTRIBUTES = [
    "user_permanent_id",
    "first_name",
    "last_name",
    "email"
]

# directory to store files during upload scanning
if os.environ.get('TMP_SCHEMA_DIR') is not None and\
        len(os.environ.get('TMP_SCHEMA_DIR')) > 0:
    TMP_SCHEMA_DIR = os.environ.get('TMP_SCHEMA_DIR')
else:
    TMP_SCHEMA_DIR = os.path.join(BASE_DIR, 'tmp', 'schemas')
TMP_SCHEMA_DIR = os.path.join(TMP_SCHEMA_DIR, '')
