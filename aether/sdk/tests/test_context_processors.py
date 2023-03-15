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

from django.test import override_settings, RequestFactory

from aether.sdk.context_processors import eha_context
from aether.sdk.tests import AetherTestCase
from aether.sdk.unittest import UrlsTestCase


class ContextProcessorsTests(AetherTestCase, UrlsTestCase):

    def test_eha_context(self):
        request = RequestFactory().get('/my-realm/sdk-app/health')
        context = eha_context(request)

        self.assertFalse(context['dev_mode'])

        self.assertEqual(context['app_name'], 'eha-test')
        self.assertEqual(context['app_name_html'], '<b>ae</b>ther')
        self.assertEqual(context['app_link'], 'http://eha-link-test')

        self.assertNotEqual(context['app_version'], '#.#.#')
        self.assertNotEqual(context['app_revision'], '---')

        # uses gateway path
        self.assertEqual(context['app_url'], '/my-realm/sdk-app')

    def test_eha_context__outside_gateway(self):
        request = RequestFactory().get('/')
        context = eha_context(request)

        self.assertEqual(context['app_url'], '/')


@override_settings(GATEWAY_ENABLED=False)
class ContextProcessorsNoGatewayTests(AetherTestCase, UrlsTestCase):

    def test_eha_context(self):
        request = RequestFactory().get('/something/sdk-app/')
        context = eha_context(request)

        self.assertEqual(context['app_url'], '/')
