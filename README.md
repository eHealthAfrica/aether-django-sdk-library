# Aether Django SDK Library

This library contains the most common features used by the different Aether django modules.

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Distribution](#distribution)
- [Tests](#tests)
- [Usage](#usage)
  - [Quick start](#quick-start)
  - [Environment variables](#environment-variables)
  - [Management commands](#management-commands)


## Requirements

This library requires **Python 3.6** and above.

Python libraries:

- [django](https://www.djangoproject.com/) As web framework. (**Above 2**)
- [django-cors-headers](https://github.com/ottoyiu/django-cors-headers)
  for handling the server headers required for Cross-Origin Resource Sharing (CORS).
- [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar)
  A configurable set of panels that display various debug information about the current request/response.
- [django-prometheus](https://github.com/korfuri/django-prometheus)
  To monitor the application with Prometheus.io.
- [django-silk](https://github.com/jazzband/django-silk)
  A live profiling and inspection tool for the Django framework.
- [django-uwsgi](https://github.com/unbit/django-uwsgi)
  Django related examples/tricks/modules for uWSGI.
- [djangorestframework](https://www.django-rest-framework.org/)
  A powerful and flexible toolkit for building Web APIs. (**Above 3.8**)
- [drf-dynamic-fields](https://github.com/dbrgn/drf-dynamic-fields)
  Dynamically select only a subset of fields per DRF resource,
  either using a whitelist or a blacklist.
- [psycopg2-binary](http://initd.org/psycopg/)
  Python-PostgreSQL Database Adapter.
- [pygments](http://pygments.org/)
  A syntax highlighting package written in Python.
- [python-json-logger](https://github.com/madzak/python-json-logger)
  A python library adding a json log formatter.
- [requests](https://2.python-requests.org//en/master/)
  HTTP for Humans.
- [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/)
  The Python Web Server Gateway Interface.

Extra dependencies (based on settings):

- **cas**
  - [django-cas-ng](https://github.com/mingchen/django-cas-ng)
    Django CAS (Central Authentication Service) client. (**Above 3.6**)

- **scheduler**
  - [django-rq](https://github.com/rq/django-rq)
    A simple app that provides django integration for RQ (Redis Queue).
  - [redis](https://github.com/andymccurdy/redis-py)
    The Python interface to the Redis key-value store.
  - [rq](https://github.com/rq/rq)
    Simple, lightweight, library for creating background jobs, and processing them.
  - [rq-scheduler](https://github.com/rq/rq-scheduler)
    Small package that adds job scheduling capabilities to RQ.

- **server**
  - [sentry-sdk](https://github.com/getsentry/sentry-python)
    Python client for Sentry.

- **storage**
  - [django-minio-storage](https://github.com/py-pa/django-minio-storage)
    A django storage driver for minio.
  - [django-storages](https://django-storages.readthedocs.io/en/latest/)
    A collection of custom storage backends for Django.
    Enabled for [boto3](https://github.com/boto/boto3) and
    [google-cloud-storage](https://github.com/googleapis/google-cloud-python).

- **test**
  - [coverage](https://coverage.readthedocs.io/)
    A tool for measuring code coverage of Python programs.
  - [flake8](http://flake8.pycqa.org/en/latest/)
    Tool For Style Guide Enforcement.
  - [flake8-quotes](https://github.com/zheller/flake8-quotes)
    Flake8 extension for checking quotes in python.
  - [tblib](https://github.com/ionelmc/python-tblib)
    Traceback serialization library.

- **webpack**
  - [django-webpack-loader](https://github.com/owais/django-webpack-loader)
    Transparently use webpack with django.

*[Return to TOC](#table-of-contents)*


## Installation

```bash
# standalone
pip3 install aether.sdk

# with extra dependencies
pip3 install aether.sdk[cas,scheduler,server,storage,test,webpack]
```

*[Return to TOC](#table-of-contents)*


## Distribution

How to create the package distribution

Execute the following command:

```bash
python3 setup.py bdist_wheel
```

or

```bash
./scripts/build.sh
```

*[Return to TOC](#table-of-contents)*


## Tests

How to test the library

First install dependencies (execute it only once):

```bash
./scripts/install.sh
```

After that execute the following command:

```bash
source ./venv/bin/activate
./scripts/test.sh
```

The file `scripts/test.ini` contains the environment variables used in the tests.

*[Return to TOC](#table-of-contents)*


## Usage

### Quick start

Add this snippet in the `settings.py` file to have the build the django application
settings based on the environment variables.

```python
# if it's an aether module
from aether.sdk.conf.settings_aether import *  # noqa

# if it's an external aether product
from aether.sdk.conf.settings import *  # noqa

# continue with the application specific settings
# and re-import the settings variables you need to reuse
# from aether.sdk.conf.settings[_aether] import WHATEVER YOU NEED TO...
```

Add this snippet in the `urls.py` file to generate default `urlpatterns`
based on the application settings.

```python
from aether.sdk.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(token=[True|False], app=[
    # include here the application/module specific URLs
])
```

Default URLs included:

  - The health endpoints:
    - the `/health` URL. Always responds with `200` status and an empty content.
      Uses `aether.sdk.health.views.health` view.
    - the `/check-db` URL. Responds with `500` status if the database is not available.
      Uses `aether.sdk.health.views.check_db` view.
    - the `/check-app` URL. Responds with current application version and more.
      Uses `aether.sdk.health.views.check_app` view.

  - the `/admin` section URLs (`ADMIN_URL` setting).
  - the `/admin/~prometheus/metrics` URL. Displays the raw monitoring data.
  - the `/admin/~uwsgi/` URL. If uWSGI is running displays the server uWSGI settings.

  - the `/accounts` URLs (`AUTH_URL` setting), checks if the REST Framework ones,
    using the templates indicated in `LOGIN_TEMPLATE` and `LOGGED_OUT_TEMPLATE`
    settings, or the Keycloak/CAS ones.

Based on the arguments:

  - `token`: indicates if the application should be able to create and return
    user tokens via POST request and activates the URL.
    The URL endpoint is indicated in the `TOKEN_URL` setting.
    Defaults to `/token`.
    Uses `aether.sdk.auth.views.auth_token` view.

    If the current user is not an admin user then creates and returns the authorization
    token for himself, otherwise creates a token for the `username` contained
    in the request payload.

Based on the application settings:

- If `DEBUG` is enabled:

  - the `debug toolbar` URLs.

- If `PROFILING_ENABLED` is set:

  - the `/admin/~silk/` URL. Displays the profiling data.

- If `EXTERNAL_APPS` is set and valid:

  - the `/check-app/{name}` URL. Checks if the external application is reachable
    with the URL and token indicated in the settings.
    Uses `aether.sdk.health.views.check_external` view.
    For `/check-app/app-name` checks if an external application server `APP_NAME`
    is reachable with the provided environment variables `APP_NAME_URL`
    and `APP_NAME_TOKEN`.

    Possible responses:
    - `500` - `Always Look on the Bright Side of Life!!!` ✘
    - `200` - `Brought to you by eHealth Africa - good tech for hard places` ✔

  - the `/check-tokens` URL. Redirects to the user tokens page if any of the
    external applications is not reachable with the URL indicated in the settings
    and the linked current user token.
    Uses `aether.sdk.health.views.health` view and the
    `aether.sdk.auth.apptoken.decorators.app_token_required` decorator.

  - the `/check-user-tokens` URL (`CHECK_TOKEN_URL` setting). Displays the external
    application tokens for the current user.
    Uses `aether.sdk.auth.apptoken.views.user_app_token_view` view and
    the template `eha/tokens.html`.

- If `APP_URL` setting is different than `/`, then the URL pattern for all
  endpoints is like: `/{app-url}/{endpoint}`.

- If `GATEWAY_ENABLED` is `True`:

  The application endpoints are also reachable with a prefixed regular expresion
  that includes the realm value and the the gateway id for this application.

  The URL pattern is like: `/{app-url}/{current-realm}/{gateway-id}/{endpoint}`.

  The authorization and admin endpoints never depend on any realm so the URLs
  use always the public realm.

  Something like:
  - `/{app-url}/{public-realm}/{gateway-id}/accounts` and
  - `/{app-url}/{public-realm}/{gateway-id}/admin`.

*[Return to TOC](#table-of-contents)*

### Environment variables

The following environment variables are used to build the application django settings.
Take a look at the [django settings](https://docs.djangoproject.com/en/2.2/ref/settings/).

Take a look at `aether/sdk/conf.settings.py` file to check the list of all
the expected environment variables.

#### App specific

- `APP_LINK`: `https://www.ehealthafrica.org`. The link that appears in the DRF web pages.
- `APP_NAME`: `eha`. The application name displayed in the web pages.
- `APP_NAME_HTML`: The HTML expression for the application name.
  Defaults to the application name.
- `APP_MODULE`: The django module that refers to this application to be included
  in the `INSTALLED_APPS` list.
- `APP_FAVICON`: `eha/images/eHA-icon.svg`. The application favicon.
- `APP_LOGO`: `eha/images/eHA-icon.svg`. The application logo.
- `APP_URL`: `/`. The application URL in the server.
  If host is `http://my-server` and the application URL is `/my-module`,
  the application enpoints will be accessible at `http://my-server/my-module/{endpoint}`.

*[Return to TOC](#table-of-contents)*

#### Generic

- `DEBUG`: Enables debug mode. Is `false` if unset or set to empty string,
  anything else is considered `true`.
- `TESTING`: Indicates if the application executes under test conditions.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `LOGGING_FORMATTER`: `json`. The application messages format.
  Possible values: `verbose` or `json`.
- `LOGGING_LEVEL`: `info`. Logging level for application messages.
  https://docs.python.org/3.7/library/logging.html#levels
- `SENTRY_DSN`: Sentry DSN (error reporting tool).
  https://docs.sentry.io
- `PRETTIFIED_CUTOFF`: `10000`. Indicates the maximum length of a prettified JSON value.
  See: `aether.sdk.utils.json_prettified(value, indent=2)` method.

##### Django

- `DJANGO_SECRET_KEY`: Django secret key for this installation (**mandatory**).
  https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-SECRET_KEY
- `LANGUAGE_CODE`: `en-us`. Language code for this installation.
  https://docs.djangoproject.com/en/2.2/ref/settings/#language-code
- `TIME_ZONE`: `UTC`. Time zone for this installation.
  https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-TIME_ZONE
- `STATIC_URL`: `/static/`. Provides a base URL for the static assets to be served from.
- `STATIC_ROOT`: `/var/www/static/`. Provides the local folder for the static assets to be served from.

##### Django Rest Framework (DRF)

- `PAGE_SIZE`: `10`. Default page size for the REST API.
- `MAX_PAGE_SIZE`: `5000`. Maximum page size for the REST API.
- `HTML_SELECT_CUTOFF`: `100`. Options size for the REST API Form select fields.

##### Database

More information in https://docs.djangoproject.com/en/2.2/ref/settings/#databases

  - `PGHOST`: Postgres host name (**mandatory**).
  - `PGPORT`: Postgres port (**mandatory**).
  - `DB_NAME`: Postgres database name (**mandatory**).
  - `PGUSER`: Postgres user (**mandatory**).
  - `PGPASSWORD`: Postgres user password (**mandatory**).
  - `DB_CONN_MAX_AGE`: The lifetime of a database connection, in seconds.

##### Endpoints

- `ADMIN_URL`: `admin`. Admin section endpoint.
- `AUTH_URL`: `accounts`. Authorization endpoints (login and logout URLs)
- `LOGIN_URL`, `/{AUTH_URL}/login`. Login URL.
- `TOKEN_URL`: `token`. Get authorization token endpoint.
- `CHECK_TOKEN_URL`: `check-user-tokens`. Check authorization tokens endpoint.

##### Templates

- `LOGIN_TEMPLATE`: `eha/login.html`. Template used in the login page.
- `LOGGED_OUT_TEMPLATE`: `eha/logged_out.html`. Template used in the logged out page.
- `DRF_API_RENDERER_TEMPLATE`: `eha/api.html`. Template used in the DRF browsable
  API renderer page.
- `DRF_ADMIN_RENDERER_TEMPLATE`: `eha/admin.html`. Template used in the DRF API
  admin renderer page.
- `KEYCLOAK_TEMPLATE`: `eha/login_realm.html`. Template used in the login step
  to get the realm and redirect to keycloak login page.
- `KEYCLOAK_BEHIND_TEMPLATE`: `eha/login_keycloak.html`. Template used in the
  login page when keycloak is enabled behind the scenes.

##### Profiling

- `PROFILING_ENABLED`: Used to indicate if the profiling tool (Silk) is enabled.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `SILKY_PYTHON_PROFILER`. Used to indicate if uses Python's built-in cProfile profiler.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `SILKY_PYTHON_PROFILER_BINARY`. Used to indicate if generates a binary `.prof` file.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `SILKY_PYTHON_PROFILER_RESULT_PATH`: `/tmp/`. Local directory where the `*.prof`
  files are stored.
- `SILKY_META`. To see what effect Silk is having on the request/response time.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `SILKY_MAX_REQUEST_BODY_SIZE`: `-1`. Silk saves the request body if its size (in bytes)
  is less than the indicated value. Any value less than `0` means no limit.
- `SILKY_MAX_RESPONSE_BODY_SIZE`: `-1`. Silk saves the response body if its size (in bytes)
  is less than the indicated value. Any value less than `0` means no limit.
- `SILKY_INTERCEPT_PERCENT`: `100`. Indicates the percentage of requests that are recorded.
- `SILKY_MAX_RECORDED_REQUESTS`: `10000`. The number of request/responses stored.
- `SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT`: `10`.

The `/admin/~silk/` URL displays the profiling data (accessible to admin users only).

See more in https://github.com/jazzband/django-silk

*[Return to TOC](#table-of-contents)*

#### File Storage System

- `STORAGE_REQUIRED`: Used to indicate if the file storage system is required.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `DJANGO_STORAGE_BACKEND`: Used to specify a
  [Default file storage system](https://docs.djangoproject.com/en/2.2/ref/settings/#default-file-storage).
  Available options: `minio`, `s3`, `gcs`.

More information in https://django-storages.readthedocs.io/en/latest/index.html

##### Minio (`DJANGO_STORAGE_BACKEND=minio`)

- `BUCKET_NAME`: Name of the bucket that will act as MEDIA folder (**mandatory**).
- `MINIO_STORAGE_ACCESS_KEY`: Minio Access Key.
- `MINIO_STORAGE_SECRET_KEY`: Minio Secret Access Key.
- `MINIO_STORAGE_ENDPOINT`: Minio server URL endpoint (without scheme).
- `MINIO_STORAGE_USE_HTTPS`: Whether to use TLS or not. Determines the scheme.
- `MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET`: Whether to create the bucket if it does not already exist.
- `MINIO_STORAGE_MEDIA_USE_PRESIGNED`: Determines if the media file URLs should be pre-signed.

See more in https://django-minio-storage.readthedocs.io/en/latest/usage

##### S3 (`DJANGO_STORAGE_BACKEND=s3`)

- `BUCKET_NAME`: Name of the bucket to use on s3 (**mandatory**). Must be unique on s3.
- `AWS_ACCESS_KEY_ID`: AWS Access Key to your s3 account.
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key to your s3 account.

##### Google Cloud Storage (`DJANGO_STORAGE_BACKEND=gcs`)

- `BUCKET_NAME`: Name of the bucket to use on gcs (**mandatory**).
  Create bucket using [Google Cloud Console](https://console.cloud.google.com/)
  and set appropriate permissions.
- `GS_ACCESS_KEY_ID`: Google Cloud Access Key.
- `GS_SECRET_ACCESS_KEY`: Google Cloud Secret Access Key.

[How to create Access Keys on Google Cloud Storage](https://cloud.google.com/storage/docs/migrating#keys)

*[Return to TOC](#table-of-contents)*

#### Scheduler

- `SCHEDULER_REQUIRED`: Used to indicate if the RQ platform is required.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `REDIS_HOST`: The redis host name (**mandatory**).
- `REDIS_PORT`: The redis port (**mandatory**).
- `REDIS_DB`: The redis database. Defaults to `0`.
- `REDIS_PASSWORD`: The redis password (**mandatory**).

*[Return to TOC](#table-of-contents)*

#### Security

- `DJANGO_ALLOWED_HOSTS`: `*`. Set `ALLOWED_HOSTS` Django setting.
  https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts
- `CSRF_COOKIE_DOMAIN`: `.ehealthafrica.org`. Set `CSRF_COOKIE_DOMAIN` Django setting.
  https://docs.djangoproject.com/en/2.2/ref/settings/#csrf-cookie-domain
- `CSRF_TRUSTED_ORIGINS`. Set `CSRF_TRUSTED_ORIGINS` Django setting.
  https://docs.djangoproject.com/en/2.2/ref/settings/#csrf-trusted-origins
- `DJANGO_USE_X_FORWARDED_HOST`: `False`. Set `USE_X_FORWARDED_HOST` Django setting.
  https://docs.djangoproject.com/en/2.2/ref/settings/#use-x-forwarded-host
- `DJANGO_USE_X_FORWARDED_PORT`: `False`. Set `USE_X_FORWARDED_PORT` Django setting.
  https://docs.djangoproject.com/en/2.2/ref/settings/#use-x-forwarded-port
- `DJANGO_HTTP_X_FORWARDED_PROTO`: `False`. If present sets `SECURE_PROXY_SSL_HEADER`
  Django setting to `('HTTP_X_FORWARDED_PROTO', 'https')`.
  https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-SECURE_PROXY_SSL_HEADER

*[Return to TOC](#table-of-contents)*

#### Webpack

- `WEBPACK_REQUIRED`: Used to indicate if the assets are served via webpack.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `WEBPACK_STATS_FILE`: `{STATIC_ROOT}webpack-stats.json`, indicates the file path
  that webpack uses to serve the different assets.

*[Return to TOC](#table-of-contents)*

#### Users & Authentication

##### Standard

The standard options are to log in via token authentication, via basic authentication
or via the standard django authentication.

*[Return to TOC](#table-of-contents)*

##### Keycloak Server

Set the `KEYCLOAK_SERVER_URL` and `KEYCLOAK_CLIENT_ID` environment variables if
you want to use Keycloak as authentication server.
`KEYCLOAK_CLIENT_ID` (defaults to `eha`) is the public client that allows
the aether module to authenticate using the Keycloak REST API.
This client id must be added to all the realms used by the aether module.
The `KEYCLOAK_SERVER_URL` must include all the path until the realm is indicated,
usually until `/auth/realms`.

There are two ways of setting up keycloak:

a) In this case the authentication process happens in the server side without
any further user interaction.
```ini
# .env file
KEYCLOAK_SERVER_URL=http://my-keycloak-server/auth/realms
KEYCLOAK_BEHIND_SCENES=true
```

b) In this case the user is redirected to the keycloak server to finish the
sign in step.
```ini
# .env file
KEYCLOAK_SERVER_URL=http://my-keycloak-server/auth/realms
KEYCLOAK_BEHIND_SCENES=
```

Read more in [Keycloak](https://www.keycloak.org).

**Note**: Multi-tenancy is automatically enabled if the authentication server
is keycloak.

*[Return to TOC](#table-of-contents)*

###### Gateway Authentication

Set `GATEWAY_SERVICE_ID` to enable gateway authentication with keycloak.
This means that the authentication is handled by a third party system
(like [Kong](https://konghq.com)) that includes in each request the JSON Web
Token (JWT) in the `GATEWAY_HEADER_TOKEN` header (defaults to `X-Oauth-Token`).
The `GATEWAY_SERVICE_ID` indicates the gateway service.

In this case the application URLs can be reached in several ways:

Trying to access the health endpoint `/health`:

- http://my-server/health using the internal URL
- http://my-gateway-server/my-realm/my-module/health using the gateway URL
  (being `my-module` the `GATEWAY_SERVICE_ID` value)

For those endpoints that don't depend on the realm and must also be available
"unprotected" we need one more environment variable:

- `GATEWAY_PUBLIC_REALM`: `-` This represents the fake realm that is not protected
  by the gateway server. In this case the authentication is handled by the other
  available options, i.e., basic, token, CAS...

The authorization and admin endpoints never depend on any realm so the final URLs
use always the public realm.

- http://my-gateway-server/-/my-module/accounts/
- http://my-gateway-server/-/my-module/admin/

*[Return to TOC](#table-of-contents)*

##### CAS Server

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the CAS integration in the application.

See more in [Django CAS client](https://github.com/mingchen/django-cas-ng).

> Note: CAS option cannot be enabled at the same time as Keycloak.

*[Return to TOC](#table-of-contents)*

#### Multi-tenancy

The technical implementation is explained in
[Multi-tenancy README](/aether/sdk/multitenancy/README.md).
Follow the instructions to enable multi-tenancy option in your application.

- `MULTITENANCY`, Enables or disables the feature, is `false` if unset or set
  to empty string, anything else is considered `true`.
- `DEFAULT_REALM`, `eha` The default realm for artefacts created
  while multi-tenancy was not enabled.
- `REALM_COOKIE`, `eha-realm` The name of the cookie that keeps the current
  tenant id in the request headers.

*[Return to TOC](#table-of-contents)*

#### External applications

- `EXTERNAL_APPS`: comma separated list with the external apps that the
  current instance must be able to connect to and interact with.
  For each value there should be the correspondent environment variables:

  - `<<EXTERNAL_APP>>_URL`: External application server URL (**mandatory**).
  - `<<EXTERNAL_APP>>_TOKEN`: External application authorization token (**mandatory**).
  - `<<EXTERNAL_APP>>_URL_TEST`: External application server URL used in tests.
    Defaults to the external application server URL.
  - `<<EXTERNAL_APP>>_TOKEN_TEST`: External application authorization token used in tests.
    Defaults to the external application authorization token.

If the `EXTERNAL_APPS` equals to `app-1,mod-ule-2,pro-d-uct-3` the expected and
mandatory environment variables are:
- `APP_1_URL`, `APP_1_TOKEN`
- `MOD_ULE_2_URL`, `MOD_ULE_2_TOKEN`
- `PRO_D_UCT_3_URL`, `PRO_D_UCT_3_TOKEN`

If the Gateway authentication is enabled instead of using the given token the
application will use the provided `GATEWAY_HEADER_TOKEN` value to communicate
with the external application when possible.

*[Return to TOC](#table-of-contents)*


### Management commands

#### To check if an URL is reachable via command line.

```bash
# arguments:
#      -u | --url        required
#      -t | --token      optional
./manage.py check_url -u=http://my-server/url/to/check
```

#### To create "admin" users via command line.

```bash
# arguments:
#      -u | --username   required
#      -p | --password   required
#      -e | --email      optional
#      -t | --token      optional
./manage.py setup_admin -u=admin -p=password -t=auth_token
```

*[Return to TOC](#table-of-contents)*
