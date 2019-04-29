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

import logging

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError
from django.utils.translation import ugettext as _

from django_eha_sdk.utils import request

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


def check_db_connection():
    try:
        connection.cursor()
    except OperationalError:
        return False
    except Exception:
        return False

    return True


def check_external_app(app):
    '''
    Checks possible connection with any application server
    '''

    try:
        url = get_external_app_url(app)
        token = get_external_app_token(app)
    except KeyError:
        logger.warning(_('"{}" app is not a registered external app.').format(app))
        return False

    try:
        # check that the server is up
        h = request(method='head', url=url)
        assert h.status_code == 403  # expected response 403 Forbidden
        logger.info(_('"{}" app server ({}) is up and responding!').format(app, url))

        try:
            # check that the token is valid
            g = request(method='get', url=url, headers={'Authorization': f'Token {token}'})
            assert g.status_code == 200, g.content
            logger.info('"{}" app token is valid!')

            return True  # it's possible to connect with server :D

        except Exception:
            logger.warning(_('"{}" app token is not valid for app server ({}).').format(app, url))
    except Exception:
        logger.warning(_('"{}" app server ({}) is not available.').format(app, url))

    return False  # it's not possible to connect with server :(


def get_external_app_url(app):
    app = app if not settings.TESTING else f'test-{app}'
    return settings.EXTERNAL_APPS[app]['url']


def get_external_app_token(app):
    app = app if not settings.TESTING else f'test-{app}'
    return settings.EXTERNAL_APPS[app]['token']
