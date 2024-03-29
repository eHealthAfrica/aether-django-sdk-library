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

import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.authtoken.models import Token

from aether.sdk.tests import AetherTestCase
from aether.sdk.tests.fakeapp.models import (
    TestModel,
    TestChildModel,
    TestGrandChildModel,
    TestNoMtModel,
)
from aether.sdk.tests.fakeapp.serializers import (
    TestModelSerializer,
    TestChildModelSerializer,
)
from aether.sdk.multitenancy.models import MtInstance
from aether.sdk.multitenancy import utils
from aether.sdk.utils import get_meta_http_name

TEST_REALM = 'realm-test'
TEST_REALM_2 = 'realm-test-2'


class MultitenancyTests(AetherTestCase):

    def setUp(self):
        super(MultitenancyTests, self).setUp()

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_user(username, email, password)
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.save(update_fields=['first_name', 'last_name'])

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM
        self.request.user = user

        self.assertTrue(self.client.login(username=username, password=password))
        self.client.cookies[settings.REALM_COOKIE] = TEST_REALM

    def tearDown(self):
        self.client.logout()
        super(MultitenancyTests, self).tearDown()

    def test_get_multitenancy_model(self):
        self.assertEqual(settings.MULTITENANCY_MODEL, 'fakeapp.TestModel')
        self.assertEqual(utils.get_multitenancy_model(), TestModel)

    def test_models(self):
        obj1 = TestModel.objects.create(name='one')
        self.assertFalse(obj1.is_accessible(TEST_REALM))
        self.assertTrue(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertEqual(obj1.get_realm(), settings.DEFAULT_REALM)

        child1 = TestChildModel.objects.create(name='child', parent=obj1)
        self.assertEqual(child1.get_mt_instance(), obj1)
        self.assertFalse(child1.is_accessible(TEST_REALM))
        self.assertTrue(child1.is_accessible(settings.DEFAULT_REALM))
        self.assertEqual(child1.get_realm(), settings.DEFAULT_REALM)

        self.assertTrue(MtInstance.objects.count() == 0)

        obj1.add_to_realm(self.request)

        self.assertTrue(MtInstance.objects.count() > 0)
        self.assertTrue(obj1.is_accessible(TEST_REALM))
        self.assertEqual(obj1.get_realm(), TEST_REALM)
        self.assertTrue(child1.is_accessible(TEST_REALM))
        self.assertEqual(child1.get_realm(), TEST_REALM)

        # grandchildren
        grandchild = TestGrandChildModel.objects.create(name='grandchild', parent=child1)
        self.assertRaises(NotImplementedError, grandchild.get_mt_instance)
        self.assertRaises(NotImplementedError, grandchild.is_accessible, TEST_REALM)
        self.assertRaises(NotImplementedError, grandchild.get_realm)

        realm1 = MtInstance.objects.get(instance=obj1)
        self.assertEqual(str(realm1), str(obj1))
        self.assertEqual(realm1.realm, TEST_REALM)

    def test_serializers(self):
        obj1 = TestModelSerializer(
            data={'name': 'a name'},
            context={'request': self.request},
        )
        self.assertTrue(obj1.is_valid(), obj1.errors)

        # check the user queryset
        self.assertFalse(utils.check_user_in_realm(self.request, self.request.user))
        self.assertEqual(obj1.fields['user'].get_queryset().count(), 0)
        # we need to add the user to current realm
        utils.add_user_to_realm(self.request, self.request.user)
        self.assertTrue(utils.check_user_in_realm(self.request, self.request.user))
        self.assertEqual(obj1.fields['user'].get_queryset().count(), 1)

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.save()
        self.assertTrue(MtInstance.objects.count() > 0)

        realm1 = MtInstance.objects.first()
        self.assertEqual(realm1.instance.pk, obj1.data['id'])
        self.assertEqual(realm1.realm, TEST_REALM)
        self.assertIn('/testtestmodel/' + str(obj1.data['id']), obj1.data['url'])
        self.assertIn('/testtestchildmodel/?parent=' + str(obj1.data['id']),
                      obj1.data['children_url'])

        # update and check user name
        obj1_upd = TestModelSerializer(
            TestModel.objects.get(pk=obj1.data['id']),
            data={'user': self.request.user.pk},
            context={'request': self.request},
            partial=True,
        )
        self.assertTrue(obj1_upd.is_valid(), obj1_upd.errors)
        obj1_upd.save()
        self.assertEqual(obj1_upd.data['uname'], 'John Doe')

        # create another TestModel instance
        obj2 = TestModel.objects.create(name='two')
        self.assertFalse(obj2.is_accessible(TEST_REALM))

        child1 = TestChildModelSerializer(context={'request': self.request})
        # obj2 is not in the child1 parent queryset
        self.assertEqual(child1.fields['parent'].get_queryset().count(), 1)
        self.assertEqual(child1.fields['parent'].get_queryset().first().pk, obj1.data['id'])

        # try to save a child with the wrong parent
        child2 = TestChildModelSerializer(
            data={'name': 'child', 'parent': str(obj2.pk)},
            context={'request': self.request},
        )
        self.assertFalse(child2.is_valid(), child2.errors)
        # {
        #      'parent': [
        #          ErrorDetail(
        #              string='Invalid pk "#" - object does not exist.',
        #              code='does_not_exist',
        #          )
        #      ]
        # }
        self.assertEqual(child2.errors['parent'][0].code, 'does_not_exist')
        self.assertEqual(str(child2.errors['parent'][0]),
                         f'Invalid pk "{obj2.pk}" - object does not exist.')

    def test_views(self):
        # create data assigned to different realms
        realm1_group = utils.get_auth_group(self.request)
        obj1 = TestModel.objects.create(name='one')
        child1 = TestChildModel.objects.create(name='child1', parent=obj1)
        obj1.add_to_realm(self.request)
        self.assertEqual(obj1.mt.realm, TEST_REALM)
        user1 = get_user_model().objects.create(username='user1')
        utils.add_user_to_realm(self.request, user1)

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM_2
        realm2_group = utils.get_auth_group(self.request)
        self.assertNotEqual(realm1_group, realm2_group)

        obj2 = TestModel.objects.create(name='two')
        child2 = TestChildModel.objects.create(name='child2', parent=obj2)
        obj2.add_to_realm(self.request)
        self.assertEqual(obj2.mt.realm, TEST_REALM_2)
        user2 = get_user_model().objects.create(username='user2')
        utils.add_user_to_realm(self.request, user2)

        # check users realm groups
        self.assertIn(realm1_group, user1.groups.all())
        self.assertIn(realm2_group, user2.groups.all())
        self.assertEqual(self.request.user.groups.count(), 0)

        self.assertNotIn(realm2_group, user1.groups.all())
        self.assertNotIn(realm1_group, user2.groups.all())

        self.assertEqual(TestModel.objects.count(), 2)
        self.assertEqual(TestChildModel.objects.count(), 2)
        self.assertEqual(get_user_model().objects.count(), 3)

        # check that views only return instances linked to "realm1"
        url = reverse('testmodel-list')
        response = self.client.get(url)
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, TEST_REALM)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        data = response.json()
        self.assertEqual(data['count'], 1)

        # detail endpoint
        url = reverse('testmodel-detail', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('testchildmodel-detail', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # is-accessible endpoint
        url = reverse('testmodel-is-accessible', kwargs={'pk': obj1.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': child1.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': 99})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # custom endpoint
        url = reverse('testmodel-custom-404', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('testchildmodel-custom-403', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('testchildmodel-custom-403', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # users
        url = reverse('user-list')
        response = self.client.get(url)
        data = response.json()
        # only user1 belongs to TEST_REALM,
        # user2 belongs to TEST_REALM_2 and
        # self.request.user belongs to none
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], user1.id, data['results'][0])

        url = reverse('user-detail', kwargs={'pk': user1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # linked to another realm "realm2" *************************************

        # detail endpoint
        url = reverse('testmodel-detail', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('testchildmodel-detail', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # is-accessible endpoint
        url = reverse('testmodel-is-accessible', kwargs={'pk': obj2.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': child2.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': 99})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # custom endpoint
        url = reverse('testmodel-custom-404', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('testchildmodel-custom-403', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url = reverse('user-detail', kwargs={'pk': user2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_current_realm(self):
        request = RequestFactory().get('/')
        self.assertEqual(utils.get_current_realm(request), settings.DEFAULT_REALM)

        meta_key = get_meta_http_name(settings.REALM_COOKIE)
        request.META[meta_key] = 'in-headers'
        self.assertEqual(utils.get_current_realm(request), 'in-headers')

        request.COOKIES[settings.REALM_COOKIE] = 'in-cookies'
        self.assertEqual(utils.get_current_realm(request), 'in-cookies')

        setattr(request, 'session', {})
        request.session[settings.REALM_COOKIE] = 'in-session'
        self.assertEqual(utils.get_current_realm(request), 'in-session')

    def test_is_accessible_by_realm(self):
        # not affected by realm value
        obj2 = TestNoMtModel.objects.create(name='two')
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj2))

        obj1 = TestModel.objects.create(name='one')
        self.assertFalse(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: settings.DEFAULT_REALM})
        self.assertEqual(utils.add_current_realm_in_headers(self.request, {}),
                         {settings.REALM_COOKIE: TEST_REALM})

        obj1.add_to_realm(self.request)
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: obj1.mt.realm})

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM_2
        self.assertEqual(obj1.mt.realm, TEST_REALM)
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: TEST_REALM})
        self.assertEqual(utils.add_current_realm_in_headers(self.request, {}),
                         {settings.REALM_COOKIE: TEST_REALM_2})
        self.assertFalse(utils.is_accessible_by_realm(self.request, obj1))

        obj1.add_to_realm(self.request)
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(obj1.mt.realm, TEST_REALM_2)
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: TEST_REALM_2})

    def test_auth(self):
        realm_group = utils.get_auth_group(self.request)
        self.assertIsNotNone(realm_group)
        self.assertEqual(realm_group.name, utils.get_current_realm(self.request))

        self.assertEqual(self.request.user.groups.count(), 0)
        # it does not complain if the user does not belong to the realm
        utils.remove_user_from_realm(self.request, self.request.user)

        utils.add_user_to_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 1)
        self.assertIn(realm_group, self.request.user.groups.all())
        utils.remove_user_from_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 0)
        self.assertNotIn(realm_group, self.request.user.groups.all())

    def test_serializers_gateway(self):
        obj1 = TestModel.objects.create(name='one')
        obj1.add_to_realm(self.request)
        child1 = TestChildModel.objects.create(name='child', parent=obj1)

        # check without gateway
        obj1_url = reverse('testmodel-detail', kwargs={'pk': obj1.pk})
        self.assertEqual(obj1_url, f'/testtestmodel/{obj1.pk}/')
        obj1_data = self.client.get(obj1_url).json()

        child1_url = reverse('testchildmodel-detail', kwargs={'pk': child1.pk})
        children_url = reverse('testchildmodel-list')
        self.assertEqual(child1_url, f'/testtestchildmodel/{child1.pk}/')
        self.assertEqual(children_url, '/testtestchildmodel/')
        child1_data = self.client.get(child1_url).json()

        self.assertIn(obj1_url, obj1_data['url'])
        self.assertIn(f'{children_url}?parent={obj1.pk}', obj1_data['children_url'])
        self.assertIn(child1_url, child1_data['url'])
        self.assertEqual(obj1_data['url'], child1_data['parent_url'])

        # check with gateway
        obj1_realm_url = reverse('testmodel-detail', kwargs={'pk': obj1.pk, 'realm': TEST_REALM})
        self.assertEqual(
            obj1_realm_url,
            f'/{TEST_REALM}/{settings.GATEWAY_SERVICE_ID}/testtestmodel/{obj1.pk}/')
        obj1_realm_data = self.client.get(obj1_realm_url).json()
        self.assertNotEqual(obj1_data, obj1_realm_data, 'url fields are different')

        child1_realm_url = reverse('testchildmodel-detail',
                                   kwargs={'pk': child1.pk, 'realm': TEST_REALM})
        self.assertEqual(
            child1_realm_url,
            f'/{TEST_REALM}/{settings.GATEWAY_SERVICE_ID}/testtestchildmodel/{child1.pk}/')

        children_realm_url = reverse('testchildmodel-list', kwargs={'realm': TEST_REALM})
        self.assertEqual(
            children_realm_url,
            f'/{TEST_REALM}/{settings.GATEWAY_SERVICE_ID}/testtestchildmodel/')

        child1_realm_data = self.client.get(child1_realm_url).json()
        self.assertNotEqual(child1_data, child1_realm_data, 'url fields are different')

        self.assertIn(obj1_realm_url, obj1_realm_data['url'])
        self.assertIn(f'{children_realm_url}?parent={obj1.pk}', obj1_realm_data['children_url'])
        self.assertIn(child1_realm_url, child1_realm_data['url'])
        self.assertEqual(obj1_realm_data['url'], child1_realm_data['parent_url'])

    def test_basic_authentication(self):
        self.client.logout()
        self.client.cookies[settings.REALM_COOKIE] = TEST_REALM

        username = 'peter-pan'
        email = 'peter-pan@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_user(f'{TEST_REALM}__{username}', email, password)

        auth_str = f'{username}:{password}'
        basic = base64.b64encode(bytearray(auth_str, 'utf-8')).decode('ascii')
        basic_headers = {'HTTP_AUTHORIZATION': f'Basic {basic}'}

        auth_str = f'{TEST_REALM}__{username}:{password}'
        basic = base64.b64encode(bytearray(auth_str, 'utf-8')).decode('ascii')
        basic_realm_headers = {'HTTP_AUTHORIZATION': f'Basic {basic}'}

        auth_str = f'{TEST_REALM_2}__{username}:{password}'
        basic = base64.b64encode(bytearray(auth_str, 'utf-8')).decode('ascii')
        basic_realm_2_headers = {'HTTP_AUTHORIZATION': f'Basic {basic}'}

        url = reverse('http-200')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'})

        response = self.client.get(url, **basic_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'Invalid user in this realm.'})

        response = self.client.get(url, **basic_realm_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'Invalid user in this realm.'})

        response = self.client.get(url, **basic_realm_2_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'Invalid username/password.'})

        utils.add_user_to_realm(self.request, user)

        response = self.client.get(url, **basic_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(url, **basic_realm_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_basic_authentication__admin(self):
        self.client.logout()
        self.client.cookies[settings.REALM_COOKIE] = TEST_REALM

        username = 'admin-pan'
        email = 'admin-pan@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(user.is_staff)

        auth_str = f'{username}:{password}'
        basic = base64.b64encode(bytearray(auth_str, 'utf-8')).decode('ascii')
        basic_headers = {'HTTP_AUTHORIZATION': f'Basic {basic}'}

        url = reverse('http-200')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'})

        response = self.client.get(url, **basic_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_token_authentication(self):
        self.client.logout()
        self.client.cookies[settings.REALM_COOKIE] = TEST_REALM

        username = 'peter-pan'
        email = 'peter-pan@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_user(f'{TEST_REALM}__{username}', email, password)
        token_key = 'token-123456'
        Token.objects.create(user=user, key=token_key)

        token_headers = {'HTTP_AUTHORIZATION': f'Token {token_key}'}
        token_headers_wrong = {'HTTP_AUTHORIZATION': 'Token 123'}

        url = reverse('http-200')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'})

        response = self.client.get(url, **token_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'Invalid user in this realm.'})

        response = self.client.get(url, **token_headers_wrong)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'Invalid token.'})

        utils.add_user_to_realm(self.request, user)

        response = self.client.get(url, **token_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_authentication__admin(self):
        self.client.logout()
        self.client.cookies[settings.REALM_COOKIE] = TEST_REALM

        username = 'admin-pan'
        email = 'admin-pan@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(user.is_staff)

        token_key = 'token-admin-123456'
        Token.objects.create(user=user, key=token_key)
        token_headers = {'HTTP_AUTHORIZATION': f'Token {token_key}'}

        url = reverse('http-200')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'})

        response = self.client.get(url, **token_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_realms_view(self):
        url = reverse('get-realms')

        # only admin users
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        username = 'admin'
        email = 'admin@example.com'
        password = 'secretsecret'
        get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        response = self.client.get(url)
        self.assertEqual(response.json(), {'realms': [settings.DEFAULT_REALM]})

        obj1 = TestModel.objects.create(name='one')
        self.assertTrue(MtInstance.objects.count() == 0)
        self.assertFalse(obj1.is_accessible(TEST_REALM))
        self.assertEqual(response.json(), {'realms': [settings.DEFAULT_REALM]})

        obj1.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() > 0)
        self.assertEqual(obj1.mt.realm, TEST_REALM)
        self.assertTrue(obj1.is_accessible(TEST_REALM))

        response = self.client.get(url)
        realms = set(response.json()['realms'])
        self.assertEqual(realms, set([TEST_REALM, settings.DEFAULT_REALM]))

    @override_settings(MULTITENANCY=False)
    def test_no_multitenancy(self, *args):
        self.assertIsNone(utils.get_multitenancy_model())
        self.assertIsNone(utils.get_current_realm(None))

        obj1 = TestModel.objects.create(name='two')
        self.assertFalse(obj1.is_accessible(TEST_REALM))
        self.assertFalse(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertIsNone(obj1.get_realm())
        self.assertTrue(MtInstance.objects.count() == 0)

        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}), {})
        self.assertEqual(utils.add_current_realm_in_headers(self.request, {}), {})

        initial_data = TestModel.objects.all()
        self.assertEqual(utils.filter_by_realm(self.request, initial_data), initial_data)

        initial_users = get_user_model().objects.all()
        self.assertEqual(utils.filter_users_by_realm(self.request, initial_users), initial_users)

        obj1.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() == 0)

        self.assertIsNone(utils.get_auth_group(self.request))
        self.assertEqual(self.request.user.groups.count(), 0)
        self.assertTrue(utils.check_user_in_realm(self.request, self.request.user))

        utils.add_user_to_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 0)
        self.assertTrue(utils.check_user_in_realm(self.request, self.request.user))

        utils.remove_user_from_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 0)
        self.assertTrue(utils.check_user_in_realm(self.request, self.request.user))

        self.client.logout()

        username = 'peter-pan'
        email = 'peter-pan@example.com'
        password = 'secretsecret'
        user = get_user_model().objects.create_user(f'{TEST_REALM}__{username}', email, password)

        token_key = 'token-123456'
        Token.objects.create(user=user, key=token_key)

        token_headers = {'HTTP_AUTHORIZATION': f'Token {token_key}'}

        auth_str = f'{username}:{password}'
        basic = base64.b64encode(bytearray(auth_str, 'utf-8')).decode('ascii')
        basic_headers = {'HTTP_AUTHORIZATION': f'Basic {basic}'}

        auth_str = f'{TEST_REALM}__{username}:{password}'
        basic = base64.b64encode(bytearray(auth_str, 'utf-8')).decode('ascii')
        basic_realm_headers = {'HTTP_AUTHORIZATION': f'Basic {basic}'}

        url = reverse('http-200')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'})

        response = self.client.get(url, **basic_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'detail': 'Invalid username/password.'})

        response = self.client.get(url, **basic_realm_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(url, **token_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        username = 'admin'
        email = 'admin@example.com'
        password = 'secretsecret'
        get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        response = self.client.get(reverse('get-realms'))
        self.assertEqual(response.json(), {'realms': [settings.NO_MULTITENANCY_REALM]})
