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

from django.conf import settings

from aether.sdk.tests import AetherTestCase


class SettingsTest(AetherTestCase):

    def test_default_variables(self):

        self.assertTrue(settings.MULTITENANCY)
        self.assertTrue(settings.TESTING)
        self.assertFalse(settings.DEBUG)

        self.assertFalse(settings.STORAGE_REQUIRED)
        self.assertFalse(settings.SCHEDULER_REQUIRED)
        self.assertTrue(settings.WEBPACK_REQUIRED)

        self.assertEqual(settings.APP_MODULE, 'aether.sdk.tests.fakeapp')
        self.assertEqual(settings.ROOT_URLCONF, 'aether.sdk.tests.urls')

        self.assertNotEqual(settings.VERSION, '#.#.#')
        self.assertNotEqual(settings.REVISION, '---')
