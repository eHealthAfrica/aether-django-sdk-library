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
DEBUG = bool(os.getenv('DEBUG'))
TESTING = bool(os.getenv('TESTING'))
SECRET_KEY = get_required('DJANGO_SECRET_KEY')

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')

USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.getenv('STATIC_ROOT', '/var/www/static/')

PRETTIFIED_CUTOFF = int(os.getenv('PRETTIFIED_CUTOFF', 10000))

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Executes each request call at least X times
# trying to avoid unexpected connection errors.
try:
    REQUEST_ERROR_RETRIES = int(os.getenv('REQUEST_ERROR_RETRIES', 3))
except ValueError:
    REQUEST_ERROR_RETRIES = 3

if REQUEST_ERROR_RETRIES < 3:     # too small
    REQUEST_ERROR_RETRIES = 3
elif REQUEST_ERROR_RETRIES > 10:  # too big
    REQUEST_ERROR_RETRIES = 10


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
    'aether.sdk',
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
                'aether.sdk.context_processors.eha_context',
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
        'aether.sdk.drf.renderers.CustomBrowsableAPIRenderer',
        'aether.sdk.drf.renderers.CustomAdminRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'aether.sdk.auth.authentication.BasicAuthentication',
        'aether.sdk.auth.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'aether.sdk.drf.pagination.CustomPagination',
    'PAGE_SIZE': int(os.getenv('PAGE_SIZE', 10)),
    'MAX_PAGE_SIZE': int(os.getenv('MAX_PAGE_SIZE', 5000)),
    'HTML_SELECT_CUTOFF': int(os.getenv('HTML_SELECT_CUTOFF', 100)),
}

DRF_DYNAMIC_FIELDS = {
    'SUPPRESS_CONTEXT_WARNING': True,
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

# the default value is 0 (non persistent connections), None means persistent
# to avoid idle connections only include the entry when required
DB_CONN_MAX_AGE = int(os.getenv('DB_CONN_MAX_AGE', 0))
if DB_CONN_MAX_AGE > 0:
    DATABASES['default']['CONN_MAX_AGE'] = DB_CONN_MAX_AGE

# With connection pool make connections persistent and disable server side cursors
ENABLE_CONNECTION_POOL = bool(os.getenv('ENABLE_CONNECTION_POOL'))
if ENABLE_CONNECTION_POOL:
    # https://docs.djangoproject.com/en/3.2/ref/databases/#transaction-pooling-server-side-cursors
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
    # https://docs.djangoproject.com/en/3.2/ref/databases/#persistent-connections
    DATABASES['default']['CONN_MAX_AGE'] = None  # persistent

    # Instead of using an external service like pgbouncer
    # to handle the connection rely on SQLAlchemy for it.
    DB_POOL_INTERNAL = bool(os.getenv('DB_POOL_INTERNAL'))
    if DB_POOL_INTERNAL:
        DATABASES['default']['ENGINE'] = 'django_postgrespool2'
        DATABASE_POOL_ARGS = {
            'pool_size': int(os.getenv('DB_POOL_INITIAL_SIZE', 20)),
            'max_overflow': int(os.getenv('DB_POOL_MAX_OVERFLOW', 80)),
            'recycle': int(os.getenv('DB_POOL_RECYCLE_SECONDS', 3600)),
            'use_lifo': bool(os.getenv('DB_POOL_USE_LIFO')),
        }


# App Configuration
# ------------------------------------------------------------------------------

APP_URL = os.getenv('APP_URL', '/')  # URL Friendly
APP_NAME = os.getenv('APP_NAME', 'eHealth Africa')
APP_NAME_HTML = os.getenv('APP_NAME_HTML', APP_NAME)
APP_LINK = os.getenv('APP_LINK', 'http://www.ehealthafrica.org')
APP_MODULE = os.getenv('APP_MODULE', '')
APP_FAVICON = os.getenv('APP_FAVICON', 'eha/images/eHA-icon.svg')
APP_LOGO = os.getenv('APP_LOGO', 'eha/images/eHA-icon.svg')

# to be overridden in each app
APP_EXTRA_STYLE = None
APP_EXTRA_META = None

LOGIN_TEMPLATE = os.getenv('LOGIN_TEMPLATE', 'eha/login.html')
LOGGED_OUT_TEMPLATE = os.getenv('LOGGED_OUT_TEMPLATE', 'eha/logged_out.html')

ADMIN_URL = os.getenv('ADMIN_URL', 'admin')
AUTH_URL = os.getenv('AUTH_URL', 'accounts')
LOGIN_URL = os.getenv('LOGIN_URL', f'/{AUTH_URL}/login')
LOGIN_REDIRECT_URL = APP_URL
TOKEN_URL = os.getenv('TOKEN_URL', 'token')
_CHECK_TOKEN_URL = os.getenv('CHECK_TOKEN_URL', 'check-user-tokens')

DRF_API_RENDERER_TEMPLATE = os.getenv('DRF_API_RENDERER_TEMPLATE', 'eha/api.html')
DRF_ADMIN_RENDERER_TEMPLATE = os.getenv('DRF_ADMIN_RENDERER_TEMPLATE', 'eha/admin.html')

# Include app module in installed apps list
if APP_MODULE:
    INSTALLED_APPS += [APP_MODULE, ]


# REDIS Configuration
# ------------------------------------------------------------------------------

SCHEDULER_REQUIRED = bool(os.getenv('SCHEDULER_REQUIRED'))
# Cache is handled by REDIS
DJANGO_USE_CACHE = bool(os.getenv('DJANGO_USE_CACHE'))

REDIS_REQUIRED = (
    bool(os.getenv('REDIS_REQUIRED')) or
    SCHEDULER_REQUIRED or
    DJANGO_USE_CACHE
)
if REDIS_REQUIRED:
    REDIS_HOST = get_required('REDIS_HOST')
    REDIS_PORT = get_required('REDIS_PORT')
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)


# Scheduler Configuration
# ------------------------------------------------------------------------------

if SCHEDULER_REQUIRED:
    INSTALLED_APPS += ['django_rq', ]

    RQ_SHOW_ADMIN_LINK = True
    RQ_QUEUES = {
        'default': {
            'HOST': REDIS_HOST,
            'PORT': REDIS_PORT,
            'DB': REDIS_DB,
            'PASSWORD': REDIS_PASSWORD,
            'DEFAULT_TIMEOUT': 300,  # 5 minutes
        },
    }


# Cache Configuration
# ------------------------------------------------------------------------------
# https://github.com/Suor/django-cacheops
# A slick ORM cache with automatic granular event-driven invalidation.

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# How often should we fetch userinfo from the Keycloak server?
USER_TOKEN_TTL = int(os.getenv('USER_TOKEN_TTL', 60 * 1))   # 1 minute
CACHE_TTL = int(os.getenv('DJANGO_CACHE_TIMEOUT', 60 * 5))  # 5 minutes

if (not TESTING) and DJANGO_USE_CACHE:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'session'

    CACHES = {
        'default': {
            'BACKEND': 'django_prometheus.cache.backends.locmem.LocMemCache',
            'LOCATION': f'aether--django--{APP_MODULE}',
            'TIMEOUT': CACHE_TTL,
        },
        SESSION_CACHE_ALIAS: {
            'BACKEND': 'django_prometheus.cache.backends.locmem.LocMemCache',
            'LOCATION': f'aether--session--{APP_MODULE}',
            'TIMEOUT': CACHE_TTL,
        },
    }

    # DO NOT UNCOMMENT!!!
    #    Can't pickle local object 'create_reverse_many_to_one_manager.<locals>.RelatedManager'
    # MIDDLEWARE = [
    #     'django.middleware.cache.UpdateCacheMiddleware',
    #     *MIDDLEWARE,
    #     'django.middleware.cache.FetchFromCacheMiddleware',
    # ]

    # trying to avoid collisions with REDIS databases
    REDIS_DB_CACHEOPS = int(os.getenv('REDIS_DB_CACHEOPS', REDIS_DB + 1))
    REDIS_DB_DJANGO = int(os.getenv('REDIS_DB_CACHE_DJANGO', REDIS_DB_CACHEOPS + 1))
    REDIS_DB_SESSION = int(os.getenv('REDIS_DB_CACHE_SESSION', REDIS_DB_DJANGO + 1))

    DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
    # Based on:  https://www.peterbe.com/plog/fastest-redis-optimization-for-django
    _CACHE_OPTIONS = {
        'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': int(os.getenv('CACHE_POOL_SIZE', 100)),
            'retry_on_timeout': True,
        },
        'IGNORE_EXCEPTIONS': True,
        'PASSWORD': REDIS_PASSWORD,
    }

    if bool(os.getenv('REDIS_DJANGO_CACHE')):
        CACHES['default'] = {
            'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
            'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_DJANGO}',
            'OPTIONS': _CACHE_OPTIONS,
            'TIMEOUT': CACHE_TTL,
        }

    if bool(os.getenv('REDIS_SESSION_CACHE')):
        CACHES[SESSION_CACHE_ALIAS] = {
            'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
            'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_SESSION}',
            'OPTIONS': _CACHE_OPTIONS,
            'TIMEOUT': CACHE_TTL,
        }

    INSTALLED_APPS += ['cacheops', ]

    CACHEOPS_ENABLED = not TESTING  # disable on tests
    CACHEOPS_LRU = bool(os.getenv('CACHEOPS_LRU'))
    CACHEOPS_DEGRADE_ON_FAILURE = True
    CACHEOPS_REDIS = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'password': REDIS_PASSWORD,
        'db': REDIS_DB_CACHEOPS,
        'socket_timeout': 3,  # connection timeout in seconds, optional
    }
    CACHEOPS_DEFAULTS = {
        # 'all' is an alias for {'get', 'fetch', 'count', 'aggregate', 'exists'}
        'ops': ('fetch', 'get', 'exists'),
        'timeout': CACHE_TTL,
        'cache_on_save': True,
    }

    CACHEOPS = {
        # users and roles
        'auth.user': {
            'ops': ('get', 'exists'),
            'timeout': 60 * 60 * 24,  # one day
        },
        'auth.permission': {},
        'auth.group': {},
        'authtoken.token': {},
        # content types
        'contenttypes.contenttype': {
            'ops': ('get', 'exists'),
            'local_get': True,  # put into local cache for faster recall
        },
        # internal models
        'apptoken.*': {},
        'multitenancy.mtinstance': {
            'ops': ('get', 'exists'),
            'timeout': 60 * 60 * 24,  # one day
        },
    }

    if APP_MODULE:
        # take the last part of the path `aether.my.module` => `module`
        _module_name = APP_MODULE.split('.')[-1]
        CACHEOPS[f'{_module_name}.*'] = {}


# Logging Configuration
# ------------------------------------------------------------------------------

# https://docs.python.org/3.7/library/logging.html#levels
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', logging.INFO)
LOGGING_CLASS = 'logging.StreamHandler' if not TESTING else 'logging.NullHandler'
LOGGING_FORMAT = '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
LOGGING_FORMATTER = os.getenv('LOGGING_FORMATTER')
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
    'filters': {
        'no_health': {
            '()': 'aether.sdk.conf.log_filter.HealthUrlFilter'
        },
        'no_static': {
            '()': 'aether.sdk.conf.log_filter.StaticUrlFilter'
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_LEVEL,
            'class': LOGGING_CLASS,
            'formatter': LOGGING_FORMATTER,
            'filters': ['no_health', 'no_static', ],
        },
    },
    'loggers': {
        APP_MODULE: {
            'level': LOGGING_LEVEL,
            'handlers': ['console', ],
            'propagate': False,
        },
        'aether': {
            'level': 'ERROR',
            'handlers': ['console', ],
            'propagate': False,
        },
        'django': {
            'level': 'ERROR',
            'handlers': ['console', ],
            'propagate': False,
        },
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['console'],
    },
}

if REDIS_REQUIRED:
    LOGGING['loggers']['redis'] = {
        'level': LOGGING_LEVEL,
        'handlers': ['console', ],
        'propagate': False,
    }

if SCHEDULER_REQUIRED:
    LOGGING['loggers']['rq.worker'] = {
        'level': LOGGING_LEVEL,
        'handlers': ['console', ],
        'propagate': False,
    }


# https://docs.sentry.io/platforms/python/django/
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    SENTRY_INTEGRATIONS = [DjangoIntegration(), ]

    if REDIS_REQUIRED:
        from sentry_sdk.integrations.redis import RedisIntegration
        SENTRY_INTEGRATIONS += [RedisIntegration(), ]

    if SCHEDULER_REQUIRED:
        from sentry_sdk.integrations.rq import RqIntegration
        SENTRY_INTEGRATIONS += [RqIntegration(), ]

    sentry_sdk.init(integrations=SENTRY_INTEGRATIONS)

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
_external_apps = os.getenv('EXTERNAL_APPS')
if _external_apps:
    for app in _external_apps.split(','):
        # get url and token to check connection to external app
        _APP = app.upper().replace('-', '_')  # my-app -> MY_APP

        url = get_required(f'{_APP}_URL')
        token = get_required(f'{_APP}_TOKEN')
        EXTERNAL_APPS[app] = {'url': url, 'token': token}

        # add key for TEST mode
        EXTERNAL_APPS[app]['test'] = {
            # url for TEST mode
            'url': os.getenv(f'{_APP}_URL_TEST', url),
            'token': os.getenv(f'{_APP}_TOKEN_TEST', token),
        }

if EXTERNAL_APPS:
    INSTALLED_APPS += ['aether.sdk.auth.apptoken', ]

    EXPOSE_HEADERS_WHITELIST = os.getenv('EXPOSE_HEADERS_WHITELIST', '')
    if not EXPOSE_HEADERS_WHITELIST or EXPOSE_HEADERS_WHITELIST == '*':
        EXPOSE_HEADERS_WHITELIST = [
            'ACCEPT',
            'ACCEPT_VERSION',
            'CONTENT_DISPOSITION',
            'CONTENT_LENGTH',
            'CONTENT_MD5',
            'CONTENT_TYPE',
            'DATE',
        ]
    else:
        EXPOSE_HEADERS_WHITELIST = EXPOSE_HEADERS_WHITELIST.split(',')

else:
    logger.info('No linked external apps!')


# Security Configuration
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_COOKIE_DOMAIN = os.getenv('CSRF_COOKIE_DOMAIN', '.ehealthafrica.org')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN

if os.getenv('DJANGO_USE_X_FORWARDED_HOST', False):
    USE_X_FORWARDED_HOST = True

if os.getenv('DJANGO_USE_X_FORWARDED_PORT', False):
    USE_X_FORWARDED_PORT = True

if os.getenv('DJANGO_HTTP_X_FORWARDED_PROTO', False):
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

KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL')
GATEWAY_ENABLED = False

if KEYCLOAK_SERVER_URL:
    KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'eha')
    KEYCLOAK_BEHIND_SCENES = bool(os.getenv('KEYCLOAK_BEHIND_SCENES'))

    DEFAULT_KEYCLOAK_TEMPLATE = 'eha/login_realm.html'
    KEYCLOAK_TEMPLATE = os.getenv('KEYCLOAK_TEMPLATE', DEFAULT_KEYCLOAK_TEMPLATE)

    DEFAULT_KEYCLOAK_BEHIND_TEMPLATE = 'eha/login_keycloak.html'
    KEYCLOAK_BEHIND_TEMPLATE = os.getenv(
        'KEYCLOAK_BEHIND_TEMPLATE',
        DEFAULT_KEYCLOAK_BEHIND_TEMPLATE)

    MIDDLEWARE += [
        'aether.sdk.auth.keycloak.middleware.TokenAuthenticationMiddleware',
    ]

    GATEWAY_SERVICE_ID = os.getenv('GATEWAY_SERVICE_ID')
    if GATEWAY_SERVICE_ID:
        GATEWAY_ENABLED = True
        GATEWAY_HEADER_TOKEN = os.getenv('GATEWAY_HEADER_TOKEN', 'X-Oauth-Token')
        GATEWAY_PUBLIC_REALM = os.getenv('GATEWAY_PUBLIC_REALM', '-')
        GATEWAY_PUBLIC_PATH = f'{GATEWAY_PUBLIC_REALM}/{GATEWAY_SERVICE_ID}'

        # the endpoints are served behind the gateway
        ADMIN_URL = os.getenv('ADMIN_URL', f'{GATEWAY_PUBLIC_PATH}/admin')
        AUTH_URL = os.getenv('AUTH_URL', f'{GATEWAY_PUBLIC_PATH}/accounts')
        LOGIN_URL = os.getenv('LOGIN_URL', f'/{AUTH_URL}/login')
        STATIC_URL = os.getenv('STATIC_URL', f'/{GATEWAY_PUBLIC_PATH}/static/')
        LOGIN_REDIRECT_URL = f'/{GATEWAY_PUBLIC_PATH}/'

        USE_X_FORWARDED_HOST = True
        USE_X_FORWARDED_PORT = True

        MIDDLEWARE += [
            'aether.sdk.auth.keycloak.middleware.GatewayAuthenticationMiddleware',
        ]

    else:
        logger.info('No Keycloak gateway enabled!')

else:
    logger.info('No Keycloak enabled!')


if GATEWAY_ENABLED:
    CHECK_TOKEN_URL = GATEWAY_PUBLIC_PATH + _CHECK_TOKEN_URL
else:
    CHECK_TOKEN_URL = APP_URL[1:] + _CHECK_TOKEN_URL


# Multitenancy Configuration
# ------------------------------------------------------------------------------

MULTITENANCY = bool(os.getenv('MULTITENANCY')) or bool(KEYCLOAK_SERVER_URL)
NO_MULTITENANCY_REALM = '~'

if MULTITENANCY:
    REALM_COOKIE = os.getenv('REALM_COOKIE', 'eha-realm')
    DEFAULT_REALM = os.getenv('DEFAULT_REALM', 'eha')

    INSTALLED_APPS += ['aether.sdk.multitenancy', ]
    MIGRATION_MODULES['multitenancy'] = 'aether.sdk.multitenancy.migrations'
    REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] += [
        'aether.sdk.multitenancy.permissions.IsAccessibleByRealm',
    ]

else:
    logger.info('No multi-tenancy enabled!')


# Storage Configuration
# ------------------------------------------------------------------------------

STORAGE_REQUIRED = bool(os.getenv('STORAGE_REQUIRED'))
if STORAGE_REQUIRED:
    # https://github.com/un1t/django-cleanup#configuration
    INSTALLED_APPS += ['django_cleanup', ]

    if TESTING:
        # we cannot rely on remote servers during tests
        # use the file system storage
        DJANGO_STORAGE_BACKEND = 'file'
        DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
        MEDIA_URL = os.getenv('MEDIA_URL_TEST', '/tmp/')
        MEDIA_ROOT = os.getenv('MEDIA_ROOT_TEST', '/tmp')

    else:
        DJANGO_STORAGE_BACKEND = os.getenv('DJANGO_STORAGE_BACKEND')
        if DJANGO_STORAGE_BACKEND not in ['minio', 's3', 'gcs']:
            msg = (
                'Unrecognized value "{}" for environment variable DJANGO_STORAGE_BACKEND.'
                ' Expected one of the following: "minio", "s3", "gcs"'
            )
            raise RuntimeError(msg.format(DJANGO_STORAGE_BACKEND))
        else:
            logger.info(f'Using storage backend "{DJANGO_STORAGE_BACKEND}"')

        if DJANGO_STORAGE_BACKEND == 'minio':
            INSTALLED_APPS += ['minio_storage', ]
            DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'

            MINIO_STORAGE_ACCESS_KEY = get_required('MINIO_STORAGE_ACCESS_KEY')
            MINIO_STORAGE_ENDPOINT = get_required('MINIO_STORAGE_ENDPOINT')
            MINIO_STORAGE_SECRET_KEY = get_required('MINIO_STORAGE_SECRET_KEY')
            MINIO_STORAGE_USE_HTTPS = bool(os.getenv('MINIO_STORAGE_USE_HTTPS'))

            MINIO_STORAGE_MEDIA_BUCKET_NAME = get_required('BUCKET_NAME')
            MINIO_STORAGE_MEDIA_URL = os.getenv('MINIO_STORAGE_MEDIA_URL')
            MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = bool(
                os.getenv('MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET')
            )
            MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY = bool(
                os.getenv('MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY')
            )
            MINIO_STORAGE_MEDIA_USE_PRESIGNED = bool(
                os.getenv('MINIO_STORAGE_MEDIA_USE_PRESIGNED')
            )
            MINIO_STORAGE_MEDIA_BACKUP_FORMAT = bool(
                os.getenv('MINIO_STORAGE_MEDIA_BACKUP_FORMAT')
            )
            MINIO_STORAGE_MEDIA_BACKUP_BUCKET = bool(
                os.getenv('MINIO_STORAGE_MEDIA_BACKUP_BUCKET')
            )

            if bool(os.getenv('COLLECT_STATIC_FILES_ON_STORAGE')):
                STATICFILES_STORAGE = 'minio_storage.storage.MinioMediaStorage'
                MINIO_STORAGE_STATIC_BUCKET_NAME = get_required('STATIC_BUCKET_NAME')

        elif DJANGO_STORAGE_BACKEND == 's3':
            INSTALLED_APPS += ['storages', ]
            DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

            AWS_STORAGE_BUCKET_NAME = get_required('BUCKET_NAME')
            AWS_S3_REGION_NAME = get_required('AWS_S3_REGION_NAME')
            AWS_DEFAULT_ACL = get_required('AWS_DEFAULT_ACL')

            if bool(os.getenv('COLLECT_STATIC_FILES_ON_STORAGE')):
                STATIC_BUCKET_NAME = get_required('STATIC_BUCKET_NAME')
                STATICFILES_STORAGE = 'aether.sdk.conf.storages.StaticS3'

        elif DJANGO_STORAGE_BACKEND == 'gcs':
            INSTALLED_APPS += ['storages', ]
            DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

            GS_BUCKET_NAME = get_required('BUCKET_NAME')

            if bool(os.getenv('COLLECT_STATIC_FILES_ON_STORAGE')):
                STATIC_BUCKET_NAME = get_required('STATIC_BUCKET_NAME')
                STATICFILES_STORAGE = 'aether.sdk.conf.storages.StaticGCS'


# Webpack Configuration
# ------------------------------------------------------------------------------

WEBPACK_REQUIRED = bool(os.getenv('WEBPACK_REQUIRED'))
if WEBPACK_REQUIRED:
    INSTALLED_APPS += ['webpack_loader', ]
    WEBPACK_STATS_FILE = os.getenv(
        'WEBPACK_STATS_FILE',
        os.path.join(STATIC_ROOT, 'webpack-stats.json')
    )
    logger.debug('Assets served by file:  {WEBPACK_STATS_FILE}')

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


# Debug Configuration
# ------------------------------------------------------------------------------

if not TESTING and DEBUG:
    INSTALLED_APPS += ['debug_toolbar', ]
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
    DEBUG_TOOLBAR_URL = os.getenv('DEBUG_TOOLBAR_URL', '__debug__')
    if GATEWAY_ENABLED:
        DEBUG_TOOLBAR_URL = os.getenv('DEBUG_TOOLBAR_URL', f'{GATEWAY_PUBLIC_PATH}/__debug__')

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_COLLAPSED': True,
        'SHOW_TOOLBAR_CALLBACK': lambda _: True,
        'ENABLE_STACKTRACES': False,
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


# Profiling Configuration
# ------------------------------------------------------------------------------

PROFILING_ENABLED = bool(os.getenv('PROFILING_ENABLED'))
if not TESTING and PROFILING_ENABLED:
    INSTALLED_APPS += ['silk', ]
    MIDDLEWARE = ['silk.middleware.SilkyMiddleware', *MIDDLEWARE, ]

    SILKY_AUTHENTICATION = True  # User must login
    SILKY_AUTHORISATION = True   # User must have permissions (is_staff)

    SILKY_PYTHON_PROFILER = bool(os.getenv('SILKY_PYTHON_PROFILER'))
    SILKY_PYTHON_PROFILER_BINARY = bool(os.getenv('SILKY_PYTHON_PROFILER_BINARY', True))
    SILKY_PYTHON_PROFILER_RESULT_PATH = os.getenv('SILKY_PYTHON_PROFILER_RESULT_PATH', '/tmp/')

    SILKY_META = bool(os.getenv('SILKY_META', True))

    SILKY_MAX_REQUEST_BODY_SIZE = int(os.getenv('SILKY_MAX_REQUEST_BODY_SIZE', -1))
    SILKY_MAX_RESPONSE_BODY_SIZE = int(os.getenv('SILKY_MAX_RESPONSE_BODY_SIZE', -1))
    SILKY_INTERCEPT_PERCENT = int(os.getenv('SILKY_INTERCEPT_PERCENT', 100))

    SILKY_MAX_RECORDED_REQUESTS = int(os.getenv('SILKY_MAX_RECORDED_REQUESTS', 10000))
    SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = int(
        os.getenv('SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT', 10)
    )


# Prometheus Configuration
# ------------------------------------------------------------------------------

if not TESTING:
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
    from .local_settings import *  # noqa
except ImportError:
    logger.debug('No local settings!')
