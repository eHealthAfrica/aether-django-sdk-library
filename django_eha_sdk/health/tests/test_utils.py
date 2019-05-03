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
from django.test import TestCase

from django_eha_sdk.health.utils import check_external_app


class UtilsTests(TestCase):

    @mock.patch('django_eha_sdk.health.utils.request',
                side_effect=[
                    mock.Mock(status_code=403),  # HEAD
                    mock.Mock(status_code=200),  # GET
                ])
    def test__check_external_app__ok(self, mock_req):
        self.assertTrue(check_external_app('app-1'))

        mock_req.assert_has_calls([
            mock.call(
                method='head',
                url=settings.EXTERNAL_APPS['app-1']['test']['url'],
            ),
            mock.call(
                method='get',
                url=settings.EXTERNAL_APPS['app-1']['test']['url'],
                headers={'Authorization': 'Token {}'.format(
                    settings.EXTERNAL_APPS['app-1']['test']['token']
                )},
            ),
        ])

    @mock.patch('django_eha_sdk.health.utils.request', return_value=mock.Mock(status_code=404))
    def test__check_external_app__head_fail(self, mock_head):
        self.assertFalse(check_external_app('app-1'))
        mock_head.assert_called_with(
            method='head',
            url=settings.EXTERNAL_APPS['app-1']['test']['url'],
        )

    @mock.patch('django_eha_sdk.health.utils.request',
                side_effect=[
                    mock.Mock(status_code=403),  # HEAD
                    mock.Mock(status_code=401),  # GET
                ])
    def test__check_external_app__get_fail(self, mock_req):
        self.assertFalse(check_external_app('app-1'))

        mock_req.assert_has_calls([
            mock.call(
                method='head',
                url=settings.EXTERNAL_APPS['app-1']['test']['url'],
            ),
            mock.call(
                method='get',
                url=settings.EXTERNAL_APPS['app-1']['test']['url'],
                headers={'Authorization': 'Token {}'.format(
                    settings.EXTERNAL_APPS['app-1']['test']['token']
                )},
            ),
        ])
