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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse, resolve

from django_eha_sdk.unittest import UrlsTestCase

user_objects = get_user_model().objects


class MockCASClient(object):
    def get_login_url(self):
        return '/login'


@override_settings(
    AUTH_URL='accounts',
    CAS_SERVER_URL='http://cas:6666',
    INSTALLED_APPS=[
        *settings.INSTALLED_APPS,
        'django_cas_ng',
        'django_eha_sdk.auth.cas',
    ],
)
class CasTests(UrlsTestCase):

    def test__urls(self):
        from django_cas_ng import views

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout/')

        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         views.LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout/').func.view_class,
                         views.LogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout/').func.view_class,
                         views.LogoutView.as_view().view_class)

    def test__workflow(self):
        # login using accounts login entrypoint
        LOGIN_URL = reverse('rest_framework:login')
        SAMPLE_URL = reverse('testmodel-list')

        # visit any page that requires authentication (without being logged)
        response = self.client.get(SAMPLE_URL)
        self.assertEqual(response.status_code, 403)

        # redirects to CAS server login page
        response = self.client.get(LOGIN_URL)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            'http://cas:6666/login?'
            'service=http%3A%2F%2Ftestserver%2Faccounts%2Flogin%2F%3Fnext%3D%252F'
        )

        user = user_objects.create_user(username='cas_testing')

        with mock.patch('django_cas_ng.views.get_service_url',
                        return_value='http://my-app/') as mock_su:
            with mock.patch('django_cas_ng.views.get_cas_client',
                            return_value=MockCASClient()) as mock_cc:
                with mock.patch('django_cas_ng.views.authenticate',
                                return_value=user) as mock_au:
                    response = self.client.get(LOGIN_URL + '?ticket=123')
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response.url, '/')

                    mock_su.assert_called_once_with(
                        mock.ANY,  # request
                        None,      # next
                    )
                    mock_cc.assert_called_once_with(
                        request=mock.ANY,
                        service_url='http://my-app/',
                    )
                    mock_au.assert_called_once_with(
                        ticket='123',
                        service='http://my-app/',
                        request=mock.ANY,
                    )
