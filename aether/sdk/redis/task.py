#!/usr/bin/env python

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

from datetime import datetime
import json
from uuid import UUID
import os
import logging
import time
import threading
from django.conf import settings
import redis
from typing import (
    Any,
    Callable,
    Dict,
    NamedTuple,
    Union
)

DEFAULT_TENANT = os.environ.get('DEFAULT_REALM', 'no-tenant')
LOG = logging.getLogger(__name__)
LOG.setLevel(settings.LOGGING_LEVEL)

KEEP_ALIVE_INTERVAL = 2


def get_settings(setting):
    if isinstance(setting, tuple):
        return setting[0]
    return setting


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)  # pragma: no cover


class Task(NamedTuple):
    id: str
    tenant: str
    type: str
    data: Union[Dict, None] = None  # None is not set


class TaskHelper(object):

    def __init__(self, settings, redis_instance=None):
        self.settings = settings
        self.redis_db = get_settings(settings.REDIS_DB)
        self.redis = redis.Redis(
            host=get_settings(settings.REDIS_HOST),
            port=get_settings(settings.REDIS_PORT),
            password=get_settings(settings.REDIS_PASSWORD),
            db=self.redis_db,
            encoding='utf-8',
            decode_responses=True
        )
        if redis_instance:
            self.redis = redis_instance
        self.pubsub = None
        self._subscribe_thread = None
        self.keep_alive = False

    # Generic Redis Task Functions
    def add(
        self,
        task: Dict[str, Any],
        type: str,
        tenant: str
    ) -> bool:
        key = '_{type}:{tenant}:{_id}'.format(
            type=type,
            _id=task['id'],
            tenant=tenant
        )
        task['modified'] = datetime.now().isoformat()
        return self.redis.set(key, json.dumps(task, cls=UUIDEncoder))

    def exists(
        self,
        _id: str,
        type: str,
        tenant: str
    ) -> bool:
        task_id = '_{type}:{tenant}:{_id}'.format(
            type=type,
            _id=_id,
            tenant=tenant
        )
        if self.redis.exists(task_id):
            return True
        return False

    def remove(
        self,
        _id: str,
        type: str,
        tenant: str
    ) -> bool:
        task_id = '_{type}:{tenant}:{_id}'.format(
            type=type,
            _id=_id,
            tenant=tenant
        )
        res = self.redis.delete(task_id)
        if not res:
            return False
        return True

    def get(
        self,
        _id: str,
        type: str,
        tenant: str
    ) -> Dict:
        task_id = f'_{type}:{tenant}:{_id}'
        return self.get_by_key(task_id)

    def get_by_key(self, key: str):
        task = self.redis.get(key)
        if not task:
            raise ValueError('No task with id {key}'.format(key=key))
        return json.loads(task)

    # subscription tasks

    def subscribe(self, callback: Callable, pattern: str, keep_alive: bool):
        self.keep_alive = keep_alive
        if not self._subscribe_thread or not self._subscribe_thread._running:
            self._init_subscriber(callback, pattern)
        else:
            self._subscribe(callback, pattern)

        if self.keep_alive:
            keep_alive_thread = threading.Thread(
                target=self.keep_alive_monitor,
                args=(callback, pattern)
            )
            keep_alive_thread.start()

    def keep_alive_monitor(self, callback, pattern):
        current_status = False
        pervious_status = True
        while self.keep_alive:
            try:
                self.pubsub.ping()
                current_status = True
            except Exception:   # pragma: no cover
                current_status = False
                LOG.debug('Redis server is down.')
            if not pervious_status and current_status:  # pragma: no cover
                LOG.debug('Restarting...')
                self._init_subscriber(callback, pattern)
            pervious_status = current_status
            time.sleep(KEEP_ALIVE_INTERVAL)

    def _init_subscriber(self, callback: Callable, pattern: str):
        LOG.debug('Initializing Redis subscriber')
        self.pubsub = self.redis.pubsub()
        self._subscribe(callback, pattern)
        self._subscribe_thread = self.pubsub.run_in_thread(sleep_time=0.1)
        LOG.debug('Subscriber Running')

    def _subscribe(self, callback: Callable, pattern: str):
        LOG.debug(f'Subscribing to {pattern}')
        keyspace = f'__keyspace@{self.redis_db}__:{pattern}'
        self.pubsub.psubscribe(**{
            f'{keyspace}': self._subscriber_wrapper(callback, keyspace)
        })
        LOG.debug(f'Added {keyspace}')

    def _subscriber_wrapper(
        self,
        fn: Callable,
        registered_channel: str
    ) -> Callable:
        # wraps the callback function so that the message instead of the event will be returned

        def wrapper(msg) -> None:
            LOG.debug(f'callback got message: {msg}')
            channel = msg['channel']
            # get _id, tenant from channel: __keyspace@0__:_test:_tenant:00001
            # where id = 00001
            channel = channel if isinstance(channel, str) else channel.decode()
            keyspace, _type, tenant, _id = channel.split(':')
            redis_data = msg['data']
            LOG.debug(f'Channel: {channel} received {redis_data};'
                      + f' registered on: {registered_channel}')
            res = None
            if redis_data not in ('set', 'del'):    # pragma: no cover
                res = Task(
                    id=_id,
                    tenant=tenant,
                    type=_type,
                    data=json.loads(redis_data)
                )
                LOG.debug(f'ID: {_id} data: {redis_data}')
            fn(res)  # On callback, hit registered function with proper data
        return wrapper

    def publish(
        self,
        task: Dict[str, Any],
        type: str,
        tenant: str
    ):
        key = '_{type}:{tenant}:{_id}'.format(
                type=type,
                _id=task['id'],
                tenant=tenant
            )
        channel = f'__keyspace@{self.redis_db}__:{key}'
        LOG.debug(f'Published to {channel}')
        return self.redis.publish(channel, json.dumps(task, cls=UUIDEncoder))

    def get_keys(self, pattern: str):
        return self.redis.execute_command('keys', pattern)
