# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
import os


def get_required(name):
    try:
        return os.environ[name]
    except KeyError as key:
        raise RuntimeError(f'Missing {key} environment variable!')


# Common Configuration
# ------------------------------------------------------------------------------

# Environment variables are false if unset or set to empty string, anything
# else is considered true.
DEBUG = bool(os.environ.get('DEBUG'))
TESTING = bool(os.environ.get('TESTING'))
SECRET_KEY = get_required('DJANGO_SECRET_KEY')

LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')

USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = os.environ.get('STATIC_URL', '/static/')
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/static/')

PRETTIFIED_CUTOFF = int(os.environ.get('PRETTIFIED_CUTOFF', 10000))


# Django Basic Configuration
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    # Basic Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    # REST framework with auth token
    'rest_framework',
    'rest_framework.authtoken',

    # CORS checking
    'corsheaders',

    # Monitoring
    'django_prometheus',
    'django_uwsgi',

    # eHA apps
    'django_eha_sdk',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_eha_sdk.context_processors.eha_context',
            ],
        },
    },
]

MIGRATION_MODULES = {}


# REST Framework Configuration
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'django_eha_sdk.drf.renderers.CustomBrowsableAPIRenderer',
        'django_eha_sdk.drf.renderers.CustomAdminRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'django_eha_sdk.drf.pagination.CustomPagination',
    'PAGE_SIZE': int(os.environ.get('PAGE_SIZE', 10)),
    'MAX_PAGE_SIZE': int(os.environ.get('MAX_PAGE_SIZE', 5000)),
    'HTML_SELECT_CUTOFF': int(os.environ.get('HTML_SELECT_CUTOFF', 100)),
}


# Database Configuration
# ------------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': get_required('DB_NAME'),
        'PASSWORD': get_required('PGPASSWORD'),
        'USER': get_required('PGUSER'),
        'HOST': get_required('PGHOST'),
        'PORT': get_required('PGPORT'),
        'TESTING': {'CHARSET': 'UTF8'},
    },
}


# App Configuration
# ------------------------------------------------------------------------------

APP_URL = os.environ.get('APP_URL', '/')  # URL Friendly
APP_NAME = os.environ.get('APP_NAME', 'eHealth Africa')
APP_NAME_HTML = os.environ.get('APP_NAME_HTML', APP_NAME)
APP_LINK = os.environ.get('APP_LINK', 'http://www.ehealthafrica.org')
APP_MODULE = os.environ.get('APP_MODULE', '')
APP_FAVICON = os.environ.get('APP_FAVICON', 'eha/images/eHA-icon.svg')
APP_LOGO = os.environ.get('APP_LOGO', 'eha/images/eHA-icon.svg')

# to be overriden in each app
APP_EXTRA_STYLE = None
APP_EXTRA_META = None

LOGIN_TEMPLATE = os.environ.get('LOGIN_TEMPLATE', 'eha/login.html')
LOGGED_OUT_TEMPLATE = os.environ.get('LOGGED_OUT_TEMPLATE', 'eha/logged_out.html')

ADMIN_URL = os.environ.get('ADMIN_URL', 'admin')
AUTH_URL = os.environ.get('AUTH_URL', 'accounts')
LOGIN_URL = os.environ.get('LOGIN_URL', f'/{AUTH_URL}/login')
LOGIN_REDIRECT_URL = APP_URL

DRF_API_RENDERER_TEMPLATE = os.environ.get('DRF_API_RENDERER_TEMPLATE', 'eha/api.html')
DRF_ADMIN_RENDERER_TEMPLATE = os.environ.get('DRF_ADMIN_RENDERER_TEMPLATE', 'eha/admin.html')

# Include app module in installed apps list
if APP_MODULE:
    INSTALLED_APPS += [APP_MODULE, ]


# Logging Configuration
# ------------------------------------------------------------------------------

# https://docs.python.org/3.7/library/logging.html#levels
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', logging.INFO)
LOGGING_CLASS = 'logging.StreamHandler' if not TESTING else 'logging.NullHandler'
LOGGING_FORMAT = '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
LOGGING_FORMATTER = os.environ.get('LOGGING_FORMATTER')
if LOGGING_FORMATTER != 'verbose':
    LOGGING_FORMATTER = 'json'

logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': LOGGING_FORMAT,
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': LOGGING_FORMAT,
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_LEVEL,
            'class': LOGGING_CLASS,
            'formatter': LOGGING_FORMATTER,
        },
    },
    'loggers': {
        APP_MODULE: {
            'level': LOGGING_LEVEL,
            'handlers': ['console', ],
            'propagate': False,
        },
        'django_eha_sdk': {
            'level': LOGGING_LEVEL,
            'handlers': ['console', ],
            'propagate': False,
        },
        'django': {
            'level': LOGGING_LEVEL,
            'handlers': ['console', ],
            'propagate': False,
        },
    },
    'root': {
        'level': LOGGING_LEVEL,
        'handlers': ['console'],
    },
}

# https://docs.sentry.io/platforms/python/django/
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), ]
    )

else:
    logger.info('No SENTRY enabled!')


# Version and revision
# ------------------------------------------------------------------------------

try:
    with open('/var/tmp/VERSION') as fp:
        VERSION = fp.read().strip()
except Exception:
    VERSION = '#.#.#'

try:
    with open('/var/tmp/REVISION') as fp:
        REVISION = fp.read().strip()
except Exception:
    REVISION = '---'


# Linked external apps
# ------------------------------------------------------------------------------

EXTERNAL_APPS = {}
_external_apps = os.environ.get('EXTERNAL_APPS')
if _external_apps:
    for app in _external_apps.split(','):
        # get url and token to check connection to external app
        APP = app.upper().replace('-', '_')  # my-app -> MY_APP

        url = get_required(f'{APP}_URL')
        token = get_required(f'{APP}_TOKEN')
        EXTERNAL_APPS[app] = {'url': url, 'token': token}

        # add key for TEST mode
        EXTERNAL_APPS[app]['test'] = {
            # url for TEST mode
            'url': os.environ.get(f'{APP}_URL_TEST', url),
            'token': os.environ.get(f'{APP}_TOKEN_TEST', token),
        }

if EXTERNAL_APPS:
    INSTALLED_APPS += ['django_eha_sdk.auth.apptoken', ]

else:
    logger.info('No linked external apps!')


# Security Configuration
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.ehealthafrica.org')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN

if os.environ.get('DJANGO_USE_X_FORWARDED_HOST', False):
    USE_X_FORWARDED_HOST = True

if os.environ.get('DJANGO_USE_X_FORWARDED_PORT', False):
    USE_X_FORWARDED_PORT = True

if os.environ.get('DJANGO_HTTP_X_FORWARDED_PROTO', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Authentication Configuration
# ------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Authentication Server Configuration
# ------------------------------------------------------------------------------

CAS_SERVER_URL = os.environ.get('CAS_SERVER_URL')
if CAS_SERVER_URL:
    INSTALLED_APPS += [
        'django_cas_ng',
        'django_eha_sdk.auth.cas',
    ]
    AUTHENTICATION_BACKENDS += [
        'django_eha_sdk.auth.cas.backends.CASRoleBackend',
    ]
    CAS_VERSION = 3
    CAS_LOGOUT_COMPLETELY = True
    HOSTNAME = get_required('HOSTNAME')

else:
    logger.info('No CAS enabled!')


KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL')
if KEYCLOAK_SERVER_URL:
    KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'eha')
    KEYCLOAK_BEHIND_SCENES = bool(os.environ.get('KEYCLOAK_BEHIND_SCENES'))

    DEFAULT_KEYCLOAK_TEMPLATE = 'eha/login_realm.html'
    KEYCLOAK_TEMPLATE = os.environ.get('KEYCLOAK_TEMPLATE', DEFAULT_KEYCLOAK_TEMPLATE)

    DEFAULT_KEYCLOAK_BEHIND_TEMPLATE = 'eha/login_keycloak.html'
    KEYCLOAK_BEHIND_TEMPLATE = os.environ.get(
        'KEYCLOAK_BEHIND_TEMPLATE',
        DEFAULT_KEYCLOAK_BEHIND_TEMPLATE)

    MIDDLEWARE += [
        'django_eha_sdk.auth.keycloak.middleware.TokenAuthenticationMiddleware',
    ]

    GATEWAY_SERVICE_ID = os.environ.get('GATEWAY_SERVICE_ID')
    if GATEWAY_SERVICE_ID:
        GATEWAY_HEADER_TOKEN = os.environ.get('GATEWAY_HEADER_TOKEN', 'X-Oauth-Token')
        GATEWAY_PUBLIC_REALM = os.environ.get('GATEWAY_PUBLIC_REALM', '-')
        GATEWAY_PUBLIC_PATH = f'{GATEWAY_PUBLIC_REALM}/{GATEWAY_SERVICE_ID}'

        # the endpoints are served behind the gateway
        ADMIN_URL = os.environ.get('ADMIN_URL', f'{GATEWAY_PUBLIC_PATH}/admin')
        AUTH_URL = os.environ.get('AUTH_URL', f'{GATEWAY_PUBLIC_PATH}/accounts')
        LOGIN_URL = os.environ.get('LOGIN_URL', f'/{AUTH_URL}/login')
        STATIC_URL = os.environ.get('STATIC_URL', f'/{GATEWAY_PUBLIC_PATH}/static/')
        LOGIN_REDIRECT_URL = f'/{GATEWAY_PUBLIC_PATH}/'

        USE_X_FORWARDED_HOST = True
        USE_X_FORWARDED_PORT = True

        MIDDLEWARE += [
            'django_eha_sdk.auth.keycloak.middleware.GatewayAuthenticationMiddleware',
        ]

    else:
        logger.info('No Keycloak gateway enabled!')

else:
    logger.info('No Keycloak enabled!')


# Multitenancy Configuration
# ------------------------------------------------------------------------------

MULTITENANCY = bool(os.environ.get('MULTITENANCY')) or bool(KEYCLOAK_SERVER_URL)
if MULTITENANCY:
    REALM_COOKIE = os.environ.get('REALM_COOKIE', 'eha-realm')
    DEFAULT_REALM = os.environ.get('DEFAULT_REALM', 'eha')

    INSTALLED_APPS += ['django_eha_sdk.multitenancy', ]
    MIGRATION_MODULES['multitenancy'] = 'django_eha_sdk.multitenancy.migrations'
    REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] += [
        'django_eha_sdk.multitenancy.permissions.IsAccessibleByRealm',
    ]

else:
    logger.info('No multi-tenancy enabled!')


# Storage Configuration
# ------------------------------------------------------------------------------

STORAGE_REQUIRED = bool(os.environ.get('STORAGE_REQUIRED'))
if STORAGE_REQUIRED:
    DJANGO_STORAGE_BACKEND = os.environ.get('DJANGO_STORAGE_BACKEND')
    if DJANGO_STORAGE_BACKEND not in ['minio', 's3', 'gcs']:
        msg = (
            'Unrecognized value "{}" for environment variable DJANGO_STORAGE_BACKEND.'
            ' Expected one of the following: "minio", "s3", "gcs"'
        )
        raise RuntimeError(msg.format(DJANGO_STORAGE_BACKEND))
    else:
        logger.info('Using storage backend "{}"'.format(DJANGO_STORAGE_BACKEND))

    if DJANGO_STORAGE_BACKEND == 'minio':
        INSTALLED_APPS += ['minio_storage', ]
        DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'

        MINIO_STORAGE_ACCESS_KEY = get_required('MINIO_STORAGE_ACCESS_KEY')
        MINIO_STORAGE_ENDPOINT = get_required('MINIO_STORAGE_ENDPOINT')
        MINIO_STORAGE_SECRET_KEY = get_required('MINIO_STORAGE_SECRET_KEY')
        MINIO_STORAGE_USE_HTTPS = bool(os.environ.get('MINIO_STORAGE_USE_HTTPS'))

        MINIO_STORAGE_MEDIA_BUCKET_NAME = get_required('BUCKET_NAME')
        MINIO_STORAGE_MEDIA_URL = os.environ.get('MINIO_STORAGE_MEDIA_URL')
        MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = bool(
            os.environ.get('MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET')
        )
        MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY = bool(
            os.environ.get('MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY')
        )
        MINIO_STORAGE_MEDIA_USE_PRESIGNED = bool(
            os.environ.get('MINIO_STORAGE_MEDIA_USE_PRESIGNED')
        )
        MINIO_STORAGE_MEDIA_BACKUP_FORMAT = bool(
            os.environ.get('MINIO_STORAGE_MEDIA_BACKUP_FORMAT')
        )
        MINIO_STORAGE_MEDIA_BACKUP_BUCKET = bool(
            os.environ.get('MINIO_STORAGE_MEDIA_BACKUP_BUCKET')
        )

    elif DJANGO_STORAGE_BACKEND == 's3':
        INSTALLED_APPS += ['storages', ]
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

        AWS_STORAGE_BUCKET_NAME = get_required('BUCKET_NAME')
        AWS_S3_REGION_NAME = get_required('AWS_S3_REGION_NAME')
        AWS_DEFAULT_ACL = get_required('AWS_DEFAULT_ACL')

    elif DJANGO_STORAGE_BACKEND == 'gcs':
        INSTALLED_APPS += ['storages', ]
        DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

        GS_BUCKET_NAME = get_required('BUCKET_NAME')


# Webpack Configuration
# ------------------------------------------------------------------------------

WEBPACK_REQUIRED = bool(os.environ.get('WEBPACK_REQUIRED'))
if WEBPACK_REQUIRED:
    INSTALLED_APPS += ['webpack_loader', ]
    WEBPACK_STATS_FILE = os.environ.get(
        'WEBPACK_STATS_FILE',
        os.path.join(STATIC_ROOT, 'webpack-stats.json')
    )
    logger.debug(f'Assets served by file:  {WEBPACK_STATS_FILE}')

    # Javascript/CSS Files:
    # https://github.com/owais/django-webpack-loader#default-configuration
    WEBPACK_LOADER = {
        'DEFAULT': {
            'CACHE': not DEBUG,
            'BUNDLE_DIR_NAME': '/',
            'STATS_FILE': WEBPACK_STATS_FILE,
            'POLL_INTERVAL': 0.1,
            'TIMEOUT': None,
            'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
        },
    }


# Scheduler Configuration
# -------------------------------------------------------------------------------

SCHEDULER_REQUIRED = bool(os.environ.get('SCHEDULER_REQUIRED'))
if SCHEDULER_REQUIRED:
    INSTALLED_APPS += ['django_rq', ]

    REDIS_HOST = get_required('REDIS_HOST')
    REDIS_PORT = get_required('REDIS_PORT')
    REDIS_DB = os.environ.get('REDIS_DB', 0)
    REDIS_PASSWORD = get_required('REDIS_PASSWORD')

    RQ_SHOW_ADMIN_LINK = True
    RQ_QUEUES = {
        'default': {
            'HOST': REDIS_HOST,
            'PORT': REDIS_PORT,
            'DB': REDIS_DB,
            'PASSWORD': REDIS_PASSWORD,
            'DEFAULT_TIMEOUT': 360,
        },
    }


# Debug Configuration
# ------------------------------------------------------------------------------

if not TESTING and DEBUG:
    INSTALLED_APPS += ['debug_toolbar', ]
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
    DEBUG_TOOLBAR_URL = os.environ.get('DEBUG_TOOLBAR_URL', '__debug__')
    if KEYCLOAK_SERVER_URL and GATEWAY_SERVICE_ID:
        DEBUG_TOOLBAR_URL = os.environ.get('DEBUG_TOOLBAR_URL', f'{GATEWAY_PUBLIC_PATH}/__debug__')

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda _: True,
        'SHOW_TEMPLATE_CONTEXT': True,
    }

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'django_uwsgi.panels.UwsgiPanel',
    ]


# Prometheus Configuration
# ------------------------------------------------------------------------------

MIDDLEWARE = [
    # Make sure this stays as the first middleware
    'django_prometheus.middleware.PrometheusBeforeMiddleware',

    *MIDDLEWARE,

    # Make sure this stays as the last middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]


# Local Configuration
# ------------------------------------------------------------------------------
# This scriptlet allows you to include custom settings in your local environment

try:
    from local_settings import *  # noqa
except ImportError:
    logger.debug('No local settings!')
