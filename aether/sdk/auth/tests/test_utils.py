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
from django.test import RequestFactory, TestCase, override_settings

from aether.sdk.auth.utils import (
    get_or_create_user,
    parse_username,
    unparse_username,
)

TEST_REALM = 'realm-test'


class UtilsTests(TestCase):

    def setUp(self):
        super(UtilsTests, self).setUp()

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM

    @override_settings(MULTITENANCY=True)
    def test_multitenancy(self, *args):
        user = get_or_create_user(self.request, username='user')
        self.assertEqual(user.username, f'{TEST_REALM}__user')

        self.assertEqual(parse_username(self.request, f'{TEST_REALM}__user'),
                         f'{TEST_REALM}__user')
        self.assertEqual(parse_username(self.request, 'user'),
                         f'{TEST_REALM}__user')

        self.assertEqual(unparse_username(self.request, f'{TEST_REALM}__user'), 'user')
        self.assertEqual(unparse_username(self.request, 'user'), 'user')

    @override_settings(MULTITENANCY=False)
    def test_no_multitenancy(self, *args):
        user = get_or_create_user(self.request, username='user')
        self.assertEqual(user.username, 'user')

        self.assertEqual(parse_username(self.request, f'{TEST_REALM}__user'),
                         f'{TEST_REALM}__user')
        self.assertEqual(parse_username(self.request, 'user'), 'user')

        self.assertEqual(unparse_username(self.request, f'{TEST_REALM}__user'),
                         f'{TEST_REALM}__user')
        self.assertEqual(unparse_username(self.request, 'user'), 'user')
