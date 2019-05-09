#!/usr/bin/env python

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

import os
from io import open
from setuptools import find_packages, setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


VERSION = os.environ.get('VERSION', '1.0.0')

setup(
    version=VERSION,
    name='django_eha_sdk',
    description='A python library with helpful django tools',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords=[
        'django',
        'setup',
        'auth',
        'cas',
        'token',
        'keycloak',
        'multitenancy',
    ],

    url='https://github.com/eHealthAfrica/django-eha-sdk/',
    author='eHealth Africa',
    author_email='info@ehealthafrica.org',
    license='Apache2 License',

    python_requires='>=3.6',
    install_requires=[
        'django>=2',
        'django-cors-headers',
        'django-debug-toolbar',
        'django-prometheus',
        'django-uwsgi',
        'djangorestframework>=3.8',
        'drf-dynamic-fields',
        'psycopg2-binary',
        'pygments',
        'python-json-logger',
        'requests',
        'urllib3>=1.25',
        'uwsgi',
    ],
    extras_require={
        'cas': [
            'django-cas-ng>=3.6',
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
            'django-minio-storage',
            'django-storages[boto3,google]',
        ],
        'test': [
            'coverage',
            'flake8',
            'flake8-quotes',
            'tblib',  # for paralell test runner
        ],
        'webpack': [
            'django-webpack-loader',
        ],
    },

    packages=find_packages(exclude=['*tests*']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

)
