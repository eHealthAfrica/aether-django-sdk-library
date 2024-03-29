#!/usr/bin/env python

# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import os
from io import open
from setuptools import find_namespace_packages, setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


VERSION = os.environ.get('VERSION', '0.0.0')

setup(
    version=VERSION,
    name='aether.sdk',
    description='A python library with helpful django tools for Aether',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords=[
        'django',
        'setup',
        'auth',
        'token',
        'keycloak',
        'multitenancy',
    ],

    url='https://github.com/eHealthAfrica/aether-django-sdk-library/',
    author='eHealth Africa',
    author_email='info@ehealthafrica.org',
    license='Apache2 License',

    python_requires='>=3.6',
    install_requires=[
        'django<4',
        'django-cors-headers',
        'django-debug-toolbar',
        'django_postgrespool2',
        'django-prometheus',
        'django-silk',
        'django-uwsgi',
        'djangorestframework>=3.8',
        'drf-dynamic-fields',
        'markdown',
        'psycopg2-binary',
        'pygments',
        'python-json-logger',
        'requests[security]',
        'SQLAlchemy<2',
        'uwsgi',
    ],
    extras_require={
        'cache': [
            'django-cacheops',
            'django-redis',
        ],
        'scheduler': [
            'django-rq',
            'redis',
            'rq',
            'rq-scheduler',
        ],
        'server': [
            'sentry-sdk',
        ],
        'storage': [
            'django-cleanup',
            'django-minio-storage',
            'django-storages[boto3,google]',
        ],
        'test': [
            'coverage',
            'flake8<6',
            'flake8-quotes',
            'tblib',  # for parallel test runner
        ],
        'webpack': [
            'django-webpack-loader',
        ],
    },

    packages=find_namespace_packages(exclude=['*tests*']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

)
