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

from unittest import mock
import os
import json

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.core.files import File
from django.conf import settings

from rest_framework.authtoken.models import Token


UserModel = get_user_model().objects


class MockRequestHeadOK:
    def raise_for_status(self):
        pass


class MockRequestHeadError:
    def raise_for_status(self):
        raise Exception


class TestSetupAdminCommand(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    def test__password_argument_is_required(self):
        self.assertRaises(
            CommandError,
            call_command,
            'setup_admin',
            stdout=self.out,
        )

        self.assertRaises(
            CommandError,
            call_command,
            'setup_admin',
            '--username=admin',
            stdout=self.out,
        )

    def test__creates_new_admin_user(self):
        self.assertFalse(UserModel.filter(username='admin_test').exists())
        call_command('setup_admin', '--username=admin_test', '-p=adminadmin', stdout=self.out)
        self.assertTrue(UserModel.filter(username='admin_test').exists())

    def test__updates_existing_user(self):
        user = UserModel.create_user(username='admin', password='adminadmin')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        call_command('setup_admin', '-p=secretsecret', stdout=self.out)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test__creates_token(self):
        self.assertFalse(UserModel.filter(username='admin').exists())
        self.assertEqual(Token.objects.all().count(), 0)
        call_command('setup_admin', '-p=adminadmin', '-t=12345', stdout=self.out)
        self.assertTrue(UserModel.filter(username='admin').exists())
        self.assertEqual(Token.objects.all().count(), 1)


class TestCheckUrlCommand(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    def test__url_argument_is_required(self):
        self.assertRaises(
            CommandError,
            call_command,
            'check_url',
            stdout=self.out,
        )

    @mock.patch('aether.sdk.management.commands.check_url.request',
                return_value=MockRequestHeadOK())
    def test__check_url__ok(self, *args):
        try:
            call_command('check_url', '--url=http://localhost', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

        try:
            call_command('check_url', '-u=http://localhost', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

        try:
            call_command('check_url', '-u=http://localhost', '-t=token-1234',
                         stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    @mock.patch('aether.sdk.management.commands.check_url.request',
                return_value=MockRequestHeadError())
    def test__check_url__error(self, *args):
        self.assertRaises(
            RuntimeError,
            call_command,
            'check_url',
            '--url=http://localhost',
            stdout=self.out,
            stderr=self.out,
        )


class TestCreateUserCommand(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    def test__required_arguments(self):
        self.assertRaises(
            CommandError,
            call_command,
            'create_user',
            stdout=self.out,
            stderr=self.out,
        )

        self.assertRaises(
            CommandError,
            call_command,
            'create_user',
            '--username=user_test',
            '--realm=test',
            stdout=self.out,
            stderr=self.out,
        )

        self.assertRaises(
            CommandError,
            call_command,
            'create_user',
            '-u=user_test',
            '-p=secretsecret',
            stdout=self.out,
            stderr=self.out,
        )

        self.assertRaises(
            CommandError,
            call_command,
            'create_user',
            '--password=secretsecret',
            '--realm=test',
            stdout=self.out,
            stderr=self.out,
        )

    @override_settings(MULTITENANCY=False)
    def test__creates_new_user(self):
        self.assertFalse(UserModel.filter(username='user_test').exists())
        call_command('create_user',
                     '-u=user_test',
                     '-p=secretsecret',
                     stdout=self.out,
                     stderr=self.out)
        self.assertTrue(UserModel.filter(username='user_test').exists())

    def test__creates_new_user_in_realm(self):
        self.assertFalse(UserModel.filter(username='user_test').exists())
        call_command('create_user',
                     '-u=user_test',
                     '-p=secretsecret',
                     '-r=test',
                     stdout=self.out,
                     stderr=self.out)
        self.assertFalse(UserModel.filter(username='user_test').exists())
        self.assertTrue(UserModel.filter(username='test__user_test').exists())

    @override_settings(MULTITENANCY=False)
    def test__updates_existing_user(self):
        user = UserModel.create_user(username='user_test', password='secretsecret')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        call_command('create_user',
                     '-u=user_test',
                     '-p=secretsecret',
                     stdout=self.out,
                     stderr=self.out)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test__updates_existing_user_in_realm(self):
        user = UserModel.create_user(username='test__user_test', password='secretsecret')
        self.assertFalse(user.groups.filter(name='test').exists())

        call_command('create_user',
                     '-u=test__user_test',
                     '-p=secretsecret',
                     '-r=test',
                     stdout=self.out,
                     stderr=self.out)
        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name='test').exists())

    @override_settings(MULTITENANCY=False)
    def test__creates_token(self):
        self.assertFalse(UserModel.filter(username='user_test').exists())
        self.assertEqual(Token.objects.all().count(), 0)
        call_command('create_user',
                     '-u=user_test',
                     '-p=secretsecret',
                     '-t=12345',
                     stdout=self.out,
                     stderr=self.out)
        self.assertTrue(UserModel.filter(username='user_test').exists())
        self.assertEqual(Token.objects.all().count(), 1)

    def test__creates_token_in_realm(self):
        self.assertFalse(UserModel.filter(username='test__user_test').exists())
        self.assertEqual(Token.objects.all().count(), 0)
        call_command('create_user',
                     '-u=user_test',
                     '-p=secretsecret',
                     '-r=test',
                     '-t=12345',
                     stdout=self.out,
                     stderr=self.out)
        self.assertTrue(UserModel.filter(username='test__user_test').exists())
        self.assertEqual(Token.objects.all().count(), 1)


class TestCdnPublishCommand(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    @mock.patch('aether.sdk.management.commands.cdn_publish.default_storage.save')
    def test_cdn_publish(self, mock_cdn_save):
        call_command('cdn_publish', stdout=self.out, stderr=self.out)
        mock_cdn_save.assert_called()

        f = File(open(settings.WEBPACK_STATS_FILE, 'r'))
        f_content = json.loads(f.read())
        self.assertIn('publicPath', f_content['chunks']['test'][0])
