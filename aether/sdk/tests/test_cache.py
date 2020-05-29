# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from aether.sdk import cache
from aether.sdk.tests import AetherTestCase
from aether.sdk.unittest import UrlsTestCase


@override_settings(DJANGO_USE_CACHE=True)
class CacheTest(AetherTestCase, UrlsTestCase):

    def tearDown(self):
        super(CacheTest, self).tearDown()
        self.client.logout()

    @mock.patch('aether.sdk.cache.clear_cache')
    def test__cache__view(self, mock_cache):
        get_user_model().objects.create_superuser(
            username='admin',
            password='secretsecret',
            email='admin@aether.org',
        )
        self.assertTrue(self.client.login(username='admin', password='secretsecret'))

        response = self.client.get(reverse('purge-cache'))
        self.assertEqual(response.status_code, 200)
        mock_cache.assert_called_once()

    def test__get_content_type(self):
        UserModel = get_user_model()

        self.assertNotIn(UserModel, cache.CONTENT_TYPE_CACHE)
        cache.get_content_type(model=UserModel)
        self.assertIn(UserModel, cache.CONTENT_TYPE_CACHE)

        # Try with a non existent model
        model = AetherTestCase
        self.assertNotIn(model, cache.CONTENT_TYPE_CACHE)
        cache.get_content_type(model=model)
        self.assertNotIn(model, cache.CONTENT_TYPE_CACHE)
