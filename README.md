# Django eHealth SDK

This library contains the most common features used by the different eHealth django apps.

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Distribution](#distribution)
- [Tests](#tests)
- [Modules](#modules)

## Requirements

This library requires **Python 3.6** and above.

Python libraries:

- [django](https://www.djangoproject.com/) As web framework. (**Above 2**)
- [django-cors-headers](https://github.com/ottoyiu/django-cors-headers)
  for handling the server headers required for Cross-Origin Resource Sharing (CORS).
- [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar)
  A configurable set of panels that display various debug information about the current request/response.
- [django-prometheus](https://github.com/korfuri/django-prometheus)
  to monitor the application with Prometheus.io.
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

Extra dependencies (based on settings):

- **cas**
  - [django-cas-ng](https://github.com/mingchen/django-cas-ng)
    Django CAS (Central Authentication Service) client. (**Above 3.6**)

- **storage**
  - [django-minio-storage](https://github.com/py-pa/django-minio-storage)
    A django storage driver for minio.
  - [django-storages](https://django-storages.readthedocs.io/en/latest/)
    A collection of custom storage backends for Django.
    Enabled for [boto3](https://github.com/boto/boto3) and
    [google-cloud-storage](https://github.com/googleapis/google-cloud-python).

- **server**
  - [sentry-sdk](https://github.com/getsentry/sentry-python)
    Python client for Sentry.
  - [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/)
    The uWSGI server.

- **scheduler**
  - [django-rq](https://github.com/rq/django-rq)
    A simple app that provides django integration for RQ (Redis Queue).
  - [redis](https://github.com/andymccurdy/redis-py)
    The Python interface to the Redis key-value store.
  - [rq](https://github.com/rq/rq)
    Simple, lightweight, library for creating background jobs, and processing them.
  - [rq-scheduler](https://github.com/rq/rq-scheduler)
    Small package that adds job scheduling capabilities to RQ.

**test**
  - [coverage](https://coverage.readthedocs.io/)
    A tool for measuring code coverage of Python programs.
  - [flake8](http://flake8.pycqa.org/en/latest/)
    Tool For Style Guide Enforcement.
  - [flake8-quotes](https://github.com/zheller/flake8-quotes)
    Flake8 extension for checking quotes in python.
  - [tblib](https://github.com/ionelmc/python-tblib)
    Traceback serialization library.

*[Return to TOC](#table-of-contents)*


## Installation

```bash
# standalone
pip install django_eha_sdk

# with extra dependencies
pip install django_eha_sdk[cas,storage,server,test]
```

Add this snippet in the `settings.py` file to have the build the django app
settings based on the environment variables.

```python
from django_eha_sdk.conf.settings import *  # noqa

# continue with the app specific settings
# and re-import the settings variables you need to reuse
# from django_eha_sdk.conf.settings import WHATEVER YOU NEED TO...
```

Add this snippet in the `urls.py` file to generate default `urlpatterns`
based on the app settings.

```python
from django_eha_sdk.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(token=True, app=[
    # include here the app specific urls
])
```

*[Return to TOC](#table-of-contents)*

## Distribution

How to create the package distribution

Execute the following command in this folder.

```bash
python setup.py bdist_wheel --universal
```

or to ease the process the build is also run within a docker container.

```bash
# using the script
# (this will run the test before building the library distribution)
./build.sh
# or manually
docker-compose run sdk build
```

*[Return to TOC](#table-of-contents)*

## Tests

How to test the library

To ease the process the tests are run within a docker container.

```bash
docker-compose run sdk test
```

*[Return to TOC](#table-of-contents)*
