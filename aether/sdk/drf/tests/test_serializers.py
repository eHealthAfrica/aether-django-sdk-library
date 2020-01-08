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
from django.test import RequestFactory, override_settings

from aether.sdk.tests import AetherTestCase
from aether.sdk.tests.fakeapp.serializers import TestUserSerializer, TestUserSerializer2

TEST_REALM = 'realm-test'


class SerializersTests(AetherTestCase):

    def setUp(self):
        super(SerializersTests, self).setUp()

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM

    def test__dynamic_fields(self):
        user_data = {
            'username': 'user',
            'email': 'user@example.com',
        }

        # no filtering
        user = TestUserSerializer(
            data=user_data,
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, user_data)

        # return only `username`
        user = TestUserSerializer(
            data=user_data,
            fields=('username', ),
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {'username': 'user'})

        # return `id` (not present) and `username`
        user = TestUserSerializer(
            data=user_data,
            fields=('id', 'username', ),
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {'username': 'user'})

        # omit `id` (not present) and `username`
        user = TestUserSerializer(
            data=user_data,
            omit=('id', 'username', ),
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {'email': 'user@example.com'})

        # include and omit same field
        user = TestUserSerializer(
            data=user_data,
            fields=('username', ),
            omit=('username', ),
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        self.assertEqual(user.data, {})

    @override_settings(MULTITENANCY=True)
    def test_username_field__multitenancy(self):
        user_data = {
            'username': 'user',
            'email': 'user@example.com',
        }

        user = TestUserSerializer(
            data=user_data,
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()

        user_obj = get_user_model().objects.get(pk=user.data['id'])
        self.assertEqual(user_obj.username, f'{TEST_REALM}__user')
        self.assertEqual(user.data['username'], 'user')

    @override_settings(MULTITENANCY=False)
    def test_username_field__no_multitenancy(self):
        user_data = {
            'username': 'user',
            'email': 'user@example.com',
        }

        user = TestUserSerializer(
            data=user_data,
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()

        user_obj = get_user_model().objects.get(pk=user.data['id'])
        self.assertEqual(user_obj.username, 'user')
        self.assertEqual(user.data['username'], 'user')

    @override_settings(MULTITENANCY=True)
    def test_user_field__multitenancy(self):
        user_data = {
            'username': 'user',
        }

        user = TestUserSerializer2(
            data=user_data,
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()

        self.assertEqual(user.data['name'], 'user')

    @override_settings(MULTITENANCY=False)
    def test_user_field__no_multitenancy(self):
        user_data = {
            'username': 'user',
            'first_name': 'John',
            'last_name': 'Doe',
        }

        user = TestUserSerializer2(
            data=user_data,
            context={'request': self.request},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()

        self.assertEqual(user.data['name'], 'John Doe')
