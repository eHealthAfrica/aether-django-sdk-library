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
from django.test import override_settings
from django.urls import reverse, resolve, exceptions

from aether.sdk.unittest import UrlsTestCase


@override_settings(
    ADMIN_URL='admin',
    AUTH_URL='accounts',
    CAS_SERVER_URL=None,
    KEYCLOAK_SERVER_URL=None,
)
class UrlsTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertEqual(reverse('health'), '/health')
        self.assertEqual(reverse('check-db'), '/check-db')
        self.assertEqual(reverse('check-app'), '/check-app')
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'check-external')
        self.assertEqual(reverse('check-external', kwargs={'name': 'my-app'}),
                         '/check-app/my-app')
        self.assertEqual(reverse('admin:index'), '/admin/')

    def test__urls__auth(self):
        self.assertEqual(reverse('rest_framework:login'), '/accounts/login')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout')
        self.assertEqual(reverse('token'), '/token')
        self.assertEqual(reverse('public-token'), '/-/sdk-app/token')
        self.assertEqual(reverse('logout'), '/logout')

    def test__urls__auth__views(self):
        from django.contrib.auth.views import LoginView, LogoutView
        from aether.sdk.auth.views import auth_token

        self.assertEqual(resolve('/accounts/login').func.view_class,
                         LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout').func.view_class,
                         LogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout').func.view_class,
                         LogoutView.as_view().view_class)
        self.assertEqual(resolve('/token').func, auth_token)
        self.assertEqual(resolve('/-/sdk-app/token').func, auth_token)


@override_settings(
    ADMIN_URL='admin',
    APP_URL='/eha',
    AUTH_URL='accounts',
)
class UrlsAppUrlTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertEqual(reverse('health'), '/eha/health')
        self.assertEqual(reverse('check-db'), '/eha/check-db')
        self.assertEqual(reverse('check-app'), '/eha/check-app')
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'check-external')
        self.assertEqual(reverse('check-external', kwargs={'name': 'my-app'}),
                         '/eha/check-app/my-app')
        self.assertEqual(reverse('admin:index'), '/eha/admin/')

    def test__urls__auth(self):
        self.assertEqual(reverse('rest_framework:login'), '/eha/accounts/login')
        self.assertEqual(reverse('rest_framework:logout'), '/eha/accounts/logout')
        self.assertEqual(reverse('token'), '/eha/token')
        self.assertEqual(reverse('logout'), '/eha/logout')


@override_settings(EXTERNAL_APPS={})
class UrlsNoExternalAppsTest(UrlsTestCase):

    def test__urls(self):
        self.assertRaises(exceptions.NoReverseMatch,
                          reverse,
                          'check-external',
                          kwargs={'name': 'my-app'})


@override_settings(TEST_TOKEN_ACTIVE=False)
class UrlsNoTokenTest(UrlsTestCase):

    def test__urls(self):
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'token')


@override_settings(
    AUTH_URL='accounts',
    CAS_SERVER_URL='http://cas:6666',
    INSTALLED_APPS=[
        *settings.INSTALLED_APPS,
        'django_cas_ng',
        'aether.sdk.auth.cas',
    ],
)
class UrlsCASServerTest(UrlsTestCase):

    def test__urls(self):
        from django_cas_ng import views

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout')

        self.assertEqual(resolve('/accounts/login').func.view_class,
                         views.LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout').func.view_class,
                         views.LogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout').func.view_class,
                         views.LogoutView.as_view().view_class)


@override_settings(
    AUTH_URL='accounts',
    CAS_SERVER_URL=None,
    KEYCLOAK_BEHIND_SCENES=True,
    KEYCLOAK_SERVER_URL='http://keycloak:6666',
)
class UrlsKeycloakServerBehindTest(UrlsTestCase):

    def test__urls(self):
        from django.contrib.auth.views import LoginView
        from aether.sdk.auth.keycloak.views import KeycloakLogoutView

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login')
        self.assertEqual(resolve('/accounts/login').func.view_class,
                         LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout').func.view_class,
                         KeycloakLogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout').func.view_class,
                         KeycloakLogoutView.as_view().view_class)


@override_settings(
    AUTH_URL='accounts',
    CAS_SERVER_URL=None,
    KEYCLOAK_BEHIND_SCENES=False,
    KEYCLOAK_SERVER_URL='http://keycloak:6666',
)
class UrlsKeycloakServerTest(UrlsTestCase):

    def test__urls(self):
        from aether.sdk.auth.keycloak.views import KeycloakLoginView, KeycloakLogoutView

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login')
        self.assertEqual(resolve('/accounts/login').func.view_class,
                         KeycloakLoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout').func.view_class,
                         KeycloakLogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout').func.view_class,
                         KeycloakLogoutView.as_view().view_class)


# using `docker-compose.yml` environment
@override_settings(
    CAS_SERVER_URL=None,
    KEYCLOAK_BEHIND_SCENES=False,
    KEYCLOAK_SERVER_URL='http://keycloak:6666',
)
class UrlsGatewayUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertEqual(reverse('health', kwargs={'realm': 'my-realm'}),
                         '/my-realm/sdk-app/health')
        self.assertEqual(resolve('/my-realm/sdk-app/health').kwargs,
                         {'realm': 'my-realm'})

        self.assertEqual(reverse('health'), '/health')
        self.assertEqual(resolve('/health').kwargs, {})

        self.assertEqual(reverse('admin:index'), '/-/sdk-app/admin/')
        self.assertEqual(reverse('rest_framework:login'), '/-/sdk-app/accounts/login')


@override_settings(GATEWAY_ENABLED=False)
class UrlsNoGatewayUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertRaises(exceptions.NoReverseMatch,
                          reverse,
                          'health',
                          kwargs={'realm': 'my-realm'})


@override_settings(ADMIN_URL='private')
class AdminUrlsUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertEqual(reverse('admin:index'), '/private/')


@override_settings(AUTH_URL='secure')
class AuthUrlsUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertEqual(reverse('rest_framework:login'), '/secure/login')
