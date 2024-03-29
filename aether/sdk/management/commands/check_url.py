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

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from aether.sdk.utils import request

MESSAGE_ERROR = _('{url} is not responding.') + '\n'
MESSAGE_OK = _('{url} is responding.') + '\n'


class Command(BaseCommand):

    help = _('Check URL.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            '-u',
            type=str,
            help=_('Indicate the url to check'),
            dest='url',
            action='store',
            required=True,
        )
        parser.add_argument(
            '--token',
            '-t',
            type=str,
            help=_('Indicate the authorization token'),
            dest='token',
            action='store',
            required=False,
        )

    def handle(self, *args, **options):
        '''
        Check URL command.
        '''

        url = options['url']
        token = options['token']

        try:
            if token:
                headers = {'Authorization': f'Token {token}'}
                response = request(method='head', url=url, headers=headers)
            else:
                response = request(method='head', url=url)

            response.raise_for_status()
            self.stdout.write(MESSAGE_OK.format(url=url))

        except Exception as err:
            self.stderr.write(MESSAGE_ERROR.format(url=url))
            self.stderr.write(str(err))
            raise RuntimeError(MESSAGE_ERROR.format(url=url))
