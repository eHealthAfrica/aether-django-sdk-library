# Copyright (C) 2021 by eHealth Africa : http://www.eHealthAfrica.org
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

import logging

from django.conf import settings


class StaticUrlFilter(logging.Filter):
    '''
    Filter out requests that start with the static url
    '''

    def filter(self, record):
        try:
            if record.module == 'basehttp':
                return record.args[0].find(' {}'.format(settings.STATIC_URL)) < 0
        except Exception:
            pass
        return True


class HealthUrlFilter(logging.Filter):
    '''
    Filter out health requests
    '''

    def filter(self, record):
        try:
            if record.module == 'basehttp':
                return record.args[0].find('GET /health') < 0
        except Exception:
            pass
        return True
