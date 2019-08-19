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


from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _


class Command(BaseCommand):

    help = _('Create user')

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            '-u',
            type=str,
            help=_('Set the username'),
            dest='username',
            action='store',
            required=True,
        )
        parser.add_argument(
            '--password',
            '-p',
            type=str,
            help=_('Set the password'),
            dest='password',
            action='store',
            required=True,
        )
        parser.add_argument(
            '--token',
            '-t',
            type=str,
            help=_('Set the token'),
            dest='token',
            action='store',
            required=False,
        )
        parser.add_argument(
            '--realm',
            '-r',
            type=str,
            help=_('Set the realm'),
            dest='realm',
            action='store',
            required=False,
        )

    def handle(self, *args, **options):
        '''
        Creates a user (in the indicated realm) and sets their auth token.
        '''

        username = options['username']
        password = options['password']
        token_key = options['token']
        realm = options['realm']

        if settings.MULTITENANCY and not realm:
            msg = _('Realm argument is required')
            self.stderr.write(msg)
            raise CommandError(msg)

        userid = username
        if settings.MULTITENANCY:
            if not username.startswith(f'{realm}__'):
                userid = f'{realm}__{username}'

        user_objects = get_user_model().objects

        # create user user if needed
        if not user_objects.filter(username=userid).exists():
            user_objects.create(username=userid)
            self.stdout.write(_('Created user "{}"').format(username))

        # update password
        user = user_objects.get(username=userid)
        user.set_password(password)
        user.save()
        self.stdout.write(_('Updated user "{}"').format(username))

        if settings.MULTITENANCY:
            # add user to realm
            group, __ = Group.objects.get_or_create(name=realm)
            user.groups.add(group)
            self.stdout.write(_('Added user "{}" to realm "{}"').format(username, realm))

        # Skips if no given token or the auth token app is not installed
        if token_key and 'rest_framework.authtoken' in settings.INSTALLED_APPS:
            from rest_framework.authtoken.models import Token

            # delete previous token
            Token.objects.filter(user=user).delete()
            self.stdout.write(_('Deleted previous token for user "{}"').format(username))

            # assign token value
            Token.objects.create(user=user, key=token_key)
            self.stdout.write(_('Created token for user "{}"').format(username))
