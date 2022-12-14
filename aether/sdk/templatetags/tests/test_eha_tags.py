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
from django.contrib.auth import get_user_model
from django.test import RequestFactory


from aether.sdk.tests import AetherTestCase
from aether.sdk.templatetags.eha_tags import get_fullname, prettified


class TagsTests(AetherTestCase):

    def test_get_fullname(self):
        user = get_user_model().objects.create()

        self.assertEqual(get_fullname(user), '')
        self.assertEqual(get_fullname(user), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.username = 'user-name'
        self.assertEqual(get_fullname(user), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = 'first'
        user.last_name = ''
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = ''
        user.last_name = 'last'
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = 'first'
        user.last_name = 'last'
        self.assertEqual(get_fullname(user), 'first last')

    def test_get_fullname__realm(self):
        request = RequestFactory().get('/')
        request.COOKIES[settings.REALM_COOKIE] = 'test'

        user = get_user_model().objects.create()

        self.assertEqual(get_fullname(user, request), '')
        self.assertEqual(get_fullname(user, request), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.username = 'user-name'
        self.assertEqual(get_fullname(user, request), str(user))
        self.assertEqual(get_fullname(user, request), user.username)

        user.username = 'test__name'
        self.assertNotEqual(get_fullname(user, request), user.username)
        self.assertEqual(get_fullname(user, request), 'name')

        request.COOKIES[settings.REALM_COOKIE] = None
        self.assertEqual(get_fullname(user, request), str(user))
        self.assertEqual(get_fullname(user, request), user.username)

        request.COOKIES[settings.REALM_COOKIE] = 'another'
        self.assertEqual(get_fullname(user, request), str(user))
        self.assertEqual(get_fullname(user, request), user.username)

    def test_prettified(self):
        data = {}
        expected = '<span class="p">{}</span>'

        pretty = str(prettified(data))
        self.assertIn(expected, pretty)
