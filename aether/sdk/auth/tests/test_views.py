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

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.authtoken.models import Token

from aether.sdk.tests import AetherTestCase
from aether.sdk.unittest import UrlsTestCase

user_objects = get_user_model().objects


@override_settings(GATEWAY_ENABLED=False, MULTITENANCY=False)
class ViewsTest(AetherTestCase, UrlsTestCase):

    def setUp(self):
        super(ViewsTest, self).setUp()

        self.token_url = reverse('token')
        self.assertEqual(self.token_url, '/token')

    def test_obtain_auth_token__as_normal_user(self):
        username = 'user'
        email = 'user@example.com'
        password = 'useruser'
        user = user_objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        # no token yet
        response = self.client.get(self.token_url)
        self.assertIsNone(response.json()['token'])

        # ignores username in payload
        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        token = response.json()['token']

        self.assertEqual(user_objects.filter(username=token_username).count(), 0)
        self.assertEqual(Token.objects.get(user=user).key, token)

        response = self.client.get(self.token_url)
        self.assertEqual(response.json()['token'], token)

    def test_obtain_auth_token__as_normal_user__with_force(self):
        username = 'user'
        email = 'user@example.com'
        password = 'useruser'
        user = user_objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        # no token yet
        response = self.client.get(self.token_url)
        self.assertIsNone(response.json()['token'])

        # force it
        response = self.client.get(self.token_url + '?force')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        token = response.json()['token']
        self.assertIsNotNone(token)

        self.assertEqual(user_objects.filter(username=username).count(), 1)
        self.assertEqual(Token.objects.get(user=user).key, token)

    def test_obtain_auth_token__as_admin(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        user_objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        token = response.json()['token']
        self.assertNotEqual(token, None)

        self.assertEqual(
            user_objects.filter(username=token_username).count(),
            1,
            'request a token for a non-existing user creates the user'
        )

        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_again = response.json()['token']
        self.assertEqual(token, token_again, 'returns the same token')

        self.assertEqual(
            user_objects.filter(username=token_username).count(),
            1,
            'request a token for an existing user does not create a new user'
        )

    def test_obtain_auth_token__raises_exception(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        user_objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        with mock.patch(
            'aether.sdk.auth.views.Token.objects.get_or_create',
            side_effect=Exception(':('),
        ):
            response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()['message'], ':(')

    def test_check_obtained_token(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        user_objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['token']

        self.client.logout()

        headers = {'HTTP_AUTHORIZATION': f'Token {token}'}
        response = self.client.get(self.token_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
