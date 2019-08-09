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

import fakeredis
import uuid
import pytest


from django.test import TestCase

from aether.sdk.redis.task import TaskHelper, get_settings, UUIDEncoder
from django.conf import settings

WAIT_FOR_REDIS = 0.5


class TaskTests(TestCase):
    test_doc = {
        'id': '000-000-000-00',
        'name': 'test_name'
    }
    redis_instance = fakeredis.FakeStrictRedis()
    task = TaskHelper(settings, redis_instance)

    def callable_func(self, msg):
        assert (msg.data['id'] == self.test_doc['id'])
        assert ('modified' in msg.data)

    def test_helper_func(self):
        assert get_settings(('tuple_test',)) == 'tuple_test'
        encoder = UUIDEncoder()
        id = uuid.uuid4()
        expected = str(id)
        assert encoder.default(id) == expected

    def test_helper_init(self):
        task = TaskHelper(settings)
        assert task is not None

    def test_add_get_exists_remove(self):
        self.task.add(self.test_doc, 'mappings', 'aether')
        assert(
            len(self.task.get_keys('_map*')) == 1
        )
        doc = self.task.get(self.test_doc['id'], 'mappings', 'aether')
        assert doc['id'] == self.test_doc['id']

        assert(
            self.task.exists(self.test_doc['id'], 'mappings', 'aether')
            is True
        )
        assert(
            self.task.exists('wrong-id', 'mappings', 'aether')
            is False
        )
        with pytest.raises(Exception):
            assert self.task.get('wrong-id', 'mappings', 'aether')

        assert (
            self.task.remove('wrong-id', 'mappings', 'aether')
            is False
        )
        assert (
            self.task.remove(self.test_doc['id'], 'mappings', 'aether')
            is True
        )
        assert(
            len(self.task.get_keys('_map*')) == 0
        )
        assert(
            self.task.exists(self.test_doc['id'], 'mappings', 'aether')
            is False
        )

    def test_subscribe(self):
        self.task.subscribe(self.callable_func, '_test*', True)
        assert(
            self.task.publish(self.test_doc, 'test', 'aether') == 1
        )

        # subscribe again
        assert(
            self.task.subscribe(self.callable_func, '_test*', False) is None
        )
