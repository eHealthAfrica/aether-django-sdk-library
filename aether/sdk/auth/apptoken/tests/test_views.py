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
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse

from aether.sdk.auth.apptoken.views import TokenProxyView
from aether.sdk.tests import AetherTestCase
from aether.sdk.unittest import UrlsTestCase
from aether.sdk.utils import get_meta_http_name


RESPONSE_MOCK = mock.Mock(
    status_code=200,
    headers={'Content-Type': 'application/json'},
)
RESPONSE_MOCK_WITH_HEADERS = mock.Mock(
    status_code=200,
    headers={
        'Access-Control-Expose-Headers': 'a, b, c',
        'Content-Type': 'application/json',
        'a': 'A',
        'b': 'B',
        'z': 'Z',
    },
)
RESPONSE_MOCK_WITH_WILDCARD = mock.Mock(
    status_code=200,
    headers={
        'Authorization': 'something',
        'Access-Control-Expose-Headers': '*',
        'Content-Type': 'application/json',
        'a': 'A',
        'b': 'B',
        'z': 'Z',
    },
)
APP_TOKEN_MOCK = mock.Mock(token='ABCDEFGH')


@override_settings(GATEWAY_ENABLED=False, MULTITENANCY=False)
class ViewsTest(AetherTestCase, UrlsTestCase):

    def setUp(self):
        super(ViewsTest, self).setUp()
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)
        self.view = TokenProxyView.as_view(app_name='app-2')

    def test_tokens_required(self):
        login_url = reverse('rest_framework:login')
        tokens_url = reverse('check-user-tokens')

        # if no logged in user...
        url = reverse('check-tokens')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'{login_url}?next=/check-tokens')

        self.assertTrue(self.client.login(username='test', password='testtest'))

        response = self.client.get(tokens_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('App tokens for test', response.content.decode('utf-8'))

        # redirects to `tokens` url if something unexpected happens
        with mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                        side_effect=RuntimeError):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, tokens_url)

        # redirects to `tokens` url if the tokens are not valid
        with mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                        return_value=None):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, tokens_url)

        # with valid tokens it does not redirect
        with mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                        return_value=APP_TOKEN_MOCK) as mock_get_app_token:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            # it checks every app in `settings.EXTERNAL_APPS`: `app-1`, `app-2`, `app-3`
            self.assertEqual(mock_get_app_token.call_count, 3)
            mock_get_app_token.assert_has_calls([
                mock.call(self.user, 'app-1'),
                mock.call(self.user, 'app-2'),
                mock.call(self.user, 'app-3'),
            ])

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token')
    def test_proxy_view_without_valid_app(self, mock_get_token):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user
        view_unknown = TokenProxyView.as_view(app_name='unknown')

        self.assertRaises(
            RuntimeError,
            view_unknown,
            request,
            path='to-get',
        )
        mock_get_token.assert_not_called()

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=None)
    def test_proxy_view_without_valid_token(self, mock_get_token):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user

        self.assertRaises(
            RuntimeError,
            self.view,
            request,
            path='to-get',
        )
        mock_get_token.assert_called_once()

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request',
                return_value=mock.Mock(status_code=204, headers={}))
    def test_proxy_view_delete(self, mock_request, mock_get_token):
        request = RequestFactory().delete('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='to-delete')

        self.assertEqual(response.status_code, 204)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='DELETE',
            url='http://app-2-test/to-delete',
            data=None,
            headers={'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK_WITH_HEADERS)
    def test_proxy_view_get(self, mock_request, mock_get_token):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='/to-get')
        # Only exposed headers are included in the proxied response
        self.assertIn('a', response)
        self.assertEqual(response['a'], 'A')
        self.assertIn('b', response)
        self.assertEqual(response['b'], 'B')
        self.assertNotIn('c', response, 'not in the headers')
        self.assertNotIn('z', response, 'not in the exposed list')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='GET',
            url='http://app-2-test/to-get',
            data=None,
            headers={'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK_WITH_WILDCARD)
    def test_proxy_view_get__wildcard(self, mock_request, mock_get_token):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='/to-get')
        # Only exposed headers are included in the proxied response
        self.assertIn('a', response)
        self.assertEqual(response['a'], 'A')
        self.assertIn('b', response)
        self.assertEqual(response['b'], 'B')
        self.assertIn('z', response)
        self.assertEqual(response['z'], 'Z')
        self.assertNotIn('Authorization', response, 'not included by wildcard')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='GET',
            url='http://app-2-test/to-get',
            data=None,
            headers={'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_head(self, mock_request, mock_get_token):
        request = RequestFactory().head('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='proxy')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='HEAD',
            url='http://app-2-test/proxy',
            data=None,
            headers={'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_options(self, mock_request, mock_get_token):
        request = RequestFactory().options('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='/to-options')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='OPTIONS',
            url='http://app-2-test/to-options',
            data=None,
            headers={'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_patch(self, mock_request, mock_get_token):
        request = RequestFactory().patch('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='to-patch')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='PATCH',
            url='http://app-2-test/to-patch',
            data=None,
            headers={'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_post(self, mock_request, mock_get_token):
        request = RequestFactory().post('/go_to_proxy',
                                        data=json.dumps({'a': 1}),
                                        content_type='application/json')
        request.user = self.user
        response = self.view(request, path='posting')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='POST',
            url='http://app-2-test/posting',
            data=b'{"a": 1}',
            headers={
                'Authorization': 'Token ABCDEFGH',
                'Content-Length': '8',
                'Content-Type': 'application/json',
            }
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_put(self, mock_request, mock_get_token):
        request = RequestFactory().put('/go_to_proxy', data='something')
        request.user = self.user
        response = self.view(request, path='putting')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='PUT',
            url='http://app-2-test/putting',
            data=b'something',
            headers={
                'Authorization': 'Token ABCDEFGH',
                'Content-Length': '9',
                'Content-Type': 'application/octet-stream',
            }
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_put_but_post(self, mock_request, mock_get_token):
        request = RequestFactory().put('/go_to_example',
                                       data='something',
                                       **{'HTTP_X_METHOD': 'POST'})
        request.user = self.user
        response = self.view(request, path='fake_put')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='POST',
            url='http://app-2-test/fake_put',
            data=b'something',
            headers={
                'Authorization': 'Token ABCDEFGH',
                'Content-Length': '9',
                'Content-Type': 'application/octet-stream',
                'X-Method': 'POST',
            }
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_put_but_other(self, mock_request, mock_get_token):
        request = RequestFactory().put('/go_to_example',
                                       data='something',
                                       **{'HTTP_X_METHOD': 'GET'})
        request.user = self.user
        response = self.view(request, path='fake_put')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='PUT',
            url='http://app-2-test/fake_put',
            data=b'something',
            headers={
                'Authorization': 'Token ABCDEFGH',
                'Content-Length': '9',
                'Content-Type': 'application/octet-stream',
                'X-Method': 'GET',
            }
        )


@override_settings(GATEWAY_ENABLED=False, MULTITENANCY=True)
class MultitenancyViewsTest(UrlsTestCase):

    def setUp(self):
        super(MultitenancyViewsTest, self).setUp()

        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)
        self.view = TokenProxyView.as_view(app_name='app-2')

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_head(self, mock_request, mock_get_token):
        request = RequestFactory().head('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='proxy')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='HEAD',
            url='http://app-2-test/proxy',
            data=None,
            headers={
                'Authorization': 'Token ABCDEFGH',
                settings.REALM_COOKIE: settings.DEFAULT_REALM,
            }
        )


class GatewayViewsTest(UrlsTestCase):

    def setUp(self):
        super(GatewayViewsTest, self).setUp()

        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)
        self.view = TokenProxyView.as_view(app_name='app-3')

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token')
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_head(self, mock_request, mock_get_token):
        FAKE_TOKEN = 'access-keycloak'
        REALM = 'testing'
        SAMPLE_URL = reverse('health', kwargs={'realm': REALM})
        headers = {get_meta_http_name(settings.GATEWAY_HEADER_TOKEN): FAKE_TOKEN}

        request = RequestFactory().head(SAMPLE_URL, **headers)
        request.user = self.user
        response = self.view(request, path='proxy')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_not_called()
        mock_request.assert_called_once_with(
            method='HEAD',
            url=f'http://app-3/{REALM}/3/proxy',
            data=None,
            headers={
                settings.GATEWAY_HEADER_TOKEN: FAKE_TOKEN,
                settings.REALM_COOKIE: REALM,
            }
        )

    @mock.patch('aether.sdk.auth.apptoken.models.AppToken.get_or_create_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_head__outside_gateway(self, mock_request, mock_get_token):
        request = RequestFactory().head('/go_to_proxy_outside')
        request.user = self.user
        response = self.view(request, path='outside')

        self.assertEqual(response.status_code, 200)
        mock_get_token.assert_called_once()
        mock_request.assert_called_once_with(
            method='HEAD',
            url='http://app-3/-/3/outside',
            data=None,
            headers={
                'Authorization': 'Token ABCDEFGH',
                settings.REALM_COOKIE: settings.DEFAULT_REALM,
            }
        )
