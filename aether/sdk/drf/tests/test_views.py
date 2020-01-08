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

import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from rest_framework import status

from aether.sdk.tests import AetherTestCase
from aether.sdk.tests.fakeapp import models
from aether.sdk.unittest import UrlsTestCase

TEST_REALM = 'realm-test'


class ViewsTest(AetherTestCase, UrlsTestCase):

    def setUp(self):
        super(ViewsTest, self).setUp()

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_user(username, email, password)

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM
        self.request.user = user

        self.assertTrue(self.client.login(username=username, password=password))
        self.client.cookies[settings.REALM_COOKIE] = TEST_REALM
        test_names = ['one', 'two', 'three']
        for i in range(3):
            parent = models.TestModel.objects.create(name=test_names[i])
            for _ in range(10):
                models.TestChildModel.objects.create(
                    name=str(random.randint(1, 100)),
                    parent=parent,
                )

    def test_delete_by_filters(self):
        org_count = models.TestChildModel.objects.count()
        parent = models.TestModel.objects.first()
        filtered_count = models.TestChildModel.objects.filter(parent=parent).count()
        self.assertEqual(org_count, 30)
        self.assertEqual(filtered_count, 10)

        url = f'{reverse("testchildmodel-filtered-delete")}?search={parent.name}'
        self.client.delete(url)
        self.assertEqual(
            models.TestChildModel.objects.count(),
            (org_count - filtered_count)
        )
        filtered_count = models.TestChildModel.objects.filter(parent=parent).count()
        self.assertEqual(filtered_count, 0)

    def test_update_by_filters(self):
        org_count = models.TestChildModel.objects.count()
        parent = models.TestModel.objects.first()
        filtered_count = models.TestChildModel.objects.filter(parent=parent).count()
        self.assertEqual(org_count, 30)
        self.assertEqual(filtered_count, 10)
        url = f'{reverse("testchildmodel-filtered-partial-update")}?search={parent.name}'
        update_fields = {
            'name': 'new-name',
        }
        response = self.client.patch(
            url,
            data=update_fields,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        [
            self.assertEqual(i.name, 'new-name')
            for i in models.TestChildModel.objects.filter(parent=parent)
        ]

        update_fields = {
            'parent': 20,
        }

        response = self.client.patch(
            url,
            data=update_fields,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid pk "20"', response.json())

        response = self.client.patch(
            url,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No values to update', response.json())
