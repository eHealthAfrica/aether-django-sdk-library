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
from django.test import RequestFactory, TestCase
from django.urls import reverse

from aether.sdk.health.utils import check_external_app, get_external_app_url
from aether.sdk.unittest import MockResponse


class UtilsTests(TestCase):

    @mock.patch('aether.sdk.health.utils.exec_request',
                side_effect=[
                    MockResponse(status_code=403),  # HEAD
                    MockResponse(status_code=200),  # GET
                ])
    def test__check_external_app__ok(self, mock_req):
        self.assertTrue(check_external_app('app-1'))

        test_url = settings.EXTERNAL_APPS['app-1']['test']['url'] + '/token'
        mock_req.assert_has_calls([
            mock.call(
                method='head',
                url=test_url,
            ),
            mock.call(
                method='get',
                url=test_url,
                headers={'Authorization': 'Token {}'.format(
                    settings.EXTERNAL_APPS['app-1']['test']['token']
                )},
            ),
        ])

    @mock.patch('aether.sdk.health.utils.exec_request',
                return_value=MockResponse(status_code=404))
    def test__check_external_app__head_fail(self, mock_head):
        self.assertFalse(check_external_app('app-1'))
        mock_head.assert_called_with(
            method='head',
            url=settings.EXTERNAL_APPS['app-1']['test']['url'] + '/token',
        )

    @mock.patch('aether.sdk.health.utils.exec_request',
                side_effect=[
                    MockResponse(status_code=403),  # HEAD
                    MockResponse(status_code=401),  # GET
                ])
    def test__check_external_app__get_fail(self, mock_req):
        self.assertFalse(check_external_app('app-1'))

        test_url = settings.EXTERNAL_APPS['app-1']['test']['url'] + '/token'
        mock_req.assert_has_calls([
            mock.call(
                method='head',
                url=test_url,
            ),
            mock.call(
                method='get',
                url=test_url,
                headers={'Authorization': 'Token {}'.format(
                    settings.EXTERNAL_APPS['app-1']['test']['token']
                )},
            ),
        ])

    def test__get_external_app_url(self):
        self.assertEqual(get_external_app_url('app-1'), 'http://app-1', 'No TEST url')
        self.assertEqual(get_external_app_url('app-2'), 'http://app-2-test', 'with TEST url')
        self.assertEqual(get_external_app_url('app-3'), 'http://app-3/-/3', 'using public realm')

        request = RequestFactory().get(reverse('health'))
        self.assertEqual(get_external_app_url('app-1', request), 'http://app-1')
        self.assertEqual(get_external_app_url('app-2', request), 'http://app-2-test')
        self.assertEqual(get_external_app_url('app-3', request), 'http://app-3/-/3')

        request = RequestFactory().get(reverse('health', kwargs={'realm': 'test'}))
        self.assertEqual(get_external_app_url('app-1', request), 'http://app-1')
        self.assertEqual(get_external_app_url('app-2', request), 'http://app-2-test')
        self.assertEqual(get_external_app_url('app-3', request), 'http://app-3/test/3',
                         'using path realm')
