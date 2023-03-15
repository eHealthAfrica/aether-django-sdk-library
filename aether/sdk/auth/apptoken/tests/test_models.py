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

from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model

from aether.sdk.tests import AetherTestCase
from aether.sdk.unittest import MockResponse

from aether.sdk.auth.apptoken.models import AppToken


get_or_create_token = AppToken.get_or_create_token


class ModelsTests(AetherTestCase):

    def setUp(self):
        super(ModelsTests, self).setUp()

        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)

    def test__unknown_app(self):
        self.assertIsNone(get_or_create_token(self.user, 'other'))

        app_token = AppToken.objects.create(user=self.user, app='other', token='ABC')
        self.assertIsNone(app_token.obtain_token())
        self.assertFalse(app_token.validate_token())
        self.assertIsNone(get_or_create_token(self.user, 'other'))

    @mock.patch('aether.sdk.auth.apptoken.models.request', return_value=MockResponse(404))
    def test__get_or_create_user_app_token__obtain__none(self, mock_request):
        self.assertIsNone(get_or_create_token(self.user, 'app-1'))
        mock_request.assert_called_once_with(
            method='post',
            url=settings.EXTERNAL_APPS['app-1']['url'] + f'/{settings.TOKEN_URL}',
            data={'username': self.user.username},
            headers={'Authorization': 'Token ' + settings.EXTERNAL_APPS['app-1']['token']},
        )

    @mock.patch('aether.sdk.auth.apptoken.models.request', return_value=MockResponse(404))
    def test_get_or_create_user_app_token__not_valid_token__obtain__none(self, mock_request):
        AppToken.objects.create(user=self.user, app='app-1', token='not-valid')

        self.assertIsNone(get_or_create_token(self.user, 'app-1'))
        test_url = settings.EXTERNAL_APPS['app-1']['url'] + f'/{settings.TOKEN_URL}'
        mock_request.assert_has_calls([
            # validate
            mock.call(
                method='get',
                url=test_url,
                headers={'Authorization': 'Token not-valid'},
            ),
            # obtain
            mock.call(
                method='post',
                url=test_url,
                data={'username': self.user.username},
                headers={'Authorization': 'Token ' + settings.EXTERNAL_APPS['app-1']['token']},
            )
        ])

    @mock.patch('aether.sdk.auth.apptoken.models.request', return_value=MockResponse(200))
    def test_get_or_create_user_app_token__valid_token(self, mock_request):
        AppToken.objects.create(user=self.user, app='app-1', token='valid')

        app_token = get_or_create_token(self.user, 'app-1')
        self.assertIsNotNone(app_token)
        self.assertEqual(app_token.token, 'valid')
        self.assertEqual(app_token.token_url,
                         settings.EXTERNAL_APPS['app-1']['url'] + f'/{settings.TOKEN_URL}')

        mock_request.assert_called_once_with(
            method='get',
            url=app_token.token_url,
            headers={'Authorization': 'Token valid'},
        )

    @mock.patch('aether.sdk.auth.apptoken.models.request',
                side_effect=[
                    # validate token
                    MockResponse(404),
                    # obtain new token
                    MockResponse(200, {'token': 'valid'}),
                ])
    def test_get_or_create_user_app_token__not_valid_token__obtain__valid(self, mock_request):
        # NOTE: "app-2" has different test environment variables
        APP2 = settings.EXTERNAL_APPS['app-2']['test']

        AppToken.objects.create(user=self.user, app='app-2', token='not-valid')

        app_token = get_or_create_token(self.user, 'app-2')
        self.assertIsNotNone(app_token)
        self.assertEqual(app_token.user, self.user)
        self.assertEqual(app_token.app, 'app-2')
        self.assertEqual(app_token.token_url, APP2['url'] + '/token')
        self.assertEqual(app_token.token, 'valid')

        mock_request.assert_has_calls([
            # validate
            mock.call(
                method='get',
                url=app_token.token_url,
                headers={'Authorization': 'Token not-valid'},
            ),
            # obtain
            mock.call(
                method='post',
                url=app_token.token_url,
                data={'username': self.user.username},
                headers={'Authorization': 'Token ' + APP2['token']},
            )
        ])
