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

from django.test import TestCase

from aether.sdk.tests.fakeapp.serializers import TestUserSerializer


class SerializersTests(TestCase):

    def test__dynamic_fields(self):
        user_data = {
            'username': 'user',
            'email': 'user@example.com',
        }

        # no filtering
        user = TestUserSerializer(data=user_data)
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, user_data)

        # return only `username`
        user = TestUserSerializer(
            data=user_data,
            fields=('username', ),
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {'username': 'user'})

        # return `id` (not present) and `username`
        user = TestUserSerializer(
            data=user_data,
            fields=('id', 'username', ),
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {'username': 'user'})

        # omit `id` (not present) and `username`
        user = TestUserSerializer(
            data=user_data,
            omit=('id', 'username', ),
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {'email': 'user@example.com'})

        # include and omit same field
        user = TestUserSerializer(
            data=user_data,
            fields=('username', ),
            omit=('username', ),
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {})
