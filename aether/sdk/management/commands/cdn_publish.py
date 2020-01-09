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

import json
import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _


class Command(BaseCommand):

    help = _(
        'Uploads webpack static files to the default django storage'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--cdn-url',
            '-u',
            type=str,
            help=_('Indicate the CDN url'),
            dest='cdn',
            action='store',
            required=True,
        )
        parser.add_argument(
            '--webpack-dir',
            '-w',
            type=str,
            help=_('Indicate the path to webpack bundles dir'),
            dest='webpack',
            action='store',
            required=True,
        )
        parser.add_argument(
            '--storage-path',
            '-s',
            type=str,
            help=_('Indicate the storage path'),
            dest='storage',
            action='store',
            required=False,
            default='',
        )

    def handle(self, *args, **options):

        cdn_url = options['cdn']
        webpack_dir = options['webpack']
        storage_path = options['storage']

        if cdn_url.endswith('/'):
            cdn_url = cdn_url[:-1]
        if storage_path.startswith('/'):
            storage_path = storage_path[1:]

        # include "publicPath" key with CDN url within webpack stats file
        with open(settings.WEBPACK_STATS_FILE, 'rb') as fp:
            stats = json.load(fp)

        stats['publicPath'] = cdn_url
        for key in stats['chunks']:
            for item in stats['chunks'][key]:
                name = item['name']
                item['publicPath'] = f'{cdn_url}/{name}'

        with open(settings.WEBPACK_STATS_FILE, 'w') as fp:
            json.dump(stats, fp)

        # publish files
        self.__publish(webpack_dir, storage_path)

    def __publish(self, local_dir, storage_path):
        for file_name in sorted(os.listdir(local_dir)):
            file_path = os.path.join(local_dir, file_name)
            if os.path.isdir(file_path):
                # include nested directories
                self.__publish(file_path, f'{storage_path}{file_name}/')
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as fp:
                    default_storage.save(f'{storage_path}{file_name}', fp)
