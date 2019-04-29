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

from django.urls import reverse
from django.test import TestCase

from rest_framework import status


class ViewsTest(TestCase):

    def test__health(self, *args):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), '')

    @mock.patch('django_eha_sdk.health.views.check_db_connection', return_value=True)
    def test__check_db_ok(self, *args):
        response = self.client.get(reverse('check-db'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode(),
            'Brought to you by eHealth Africa - good tech for hard places',
        )

    @mock.patch('django_eha_sdk.health.views.check_db_connection', return_value=False)
    def test__check_db_down(self, *args):
        response = self.client.get(reverse('check-db'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.content.decode(),
            'Always Look on the Bright Side of Life!!!',
        )

    def test__check_app(self, *args):
        response = self.client.get(reverse('check-app'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        app_status = response.json()

        self.assertEqual(app_status['app_name'], 'eha-test')
        self.assertNotEqual(app_status['app_version'], '#.#.#')
        self.assertNotEqual(app_status['app_revision'], '---')

    def test__check_external_app__missing_app(self):
        # "my-app" is not an external app
        url = reverse('check-external', kwargs={'name': 'my-app'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.content.decode(),
            'Always Look on the Bright Side of Life!!!',
        )

    def test__check_external_app__error(self):
        # "app-1" is an external app
        url = reverse('check-external', kwargs={'name': 'app-1'})
        with mock.patch('django_eha_sdk.health.views.check_external_app', return_value=False):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.content.decode(),
                'Always Look on the Bright Side of Life!!!',
            )

    def test__check_external_app__ok(self):
        # "app-2" is also an external app
        url = reverse('check-external', kwargs={'name': 'app-2'})
        with mock.patch('django_eha_sdk.health.views.check_external_app', return_value=True):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.content.decode(),
                'Brought to you by eHealth Africa - good tech for hard places',
            )
