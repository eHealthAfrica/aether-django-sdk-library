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
from django.utils.translation import gettext_lazy as _

from aether.sdk.utils import request as exec_request
from aether.sdk.multitenancy.utils import get_path_realm


logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)

MSG_EXTERNAL_APP_ERR = _('"{app}" app is not registered as external app.')
MSG_EXTERNAL_APP_UP = _('"{app}" app server ({url}) is up and responding!')
MSG_EXTERNAL_APP_TOKEN_ERR = _('"{app}" app token is not valid for app server ({url}).')
MSG_EXTERNAL_APP_SERVER_ERR = _('"{app}" app server ({url}) is not available.')
MSG_EXTERNAL_APP_TOKEN_OK = _('"{app}" app token is valid for app server ({url})!')


def check_db_connection():
    try:
        connection.cursor()
    except OperationalError:
        return False
    except Exception:
        return False

    return True


def check_external_app(app, request=None):
    '''
    Checks possible connection with any application server
    '''

    try:
        url = get_external_app_url(app, request) + '/' + settings.TOKEN_URL
        token = get_external_app_token(app)
    except KeyError:
        logger.warning(MSG_EXTERNAL_APP_ERR.format(app=app))
        return False

    try:
        # check that the server is up
        h = exec_request(method='head', url=url)
        assert h.status_code == 403  # expected response 403 Forbidden
        logger.info(MSG_EXTERNAL_APP_UP.format(app=app, url=url))

        try:
            # check that the token is valid
            g = exec_request(method='get', url=url, headers={'Authorization': f'Token {token}'})
            g.raise_for_status()  # expected response 200 OK
            logger.info(MSG_EXTERNAL_APP_TOKEN_OK.format(app=app, url=url))

            return True  # it's possible to connect with server :D

        except Exception:
            logger.warning(MSG_EXTERNAL_APP_TOKEN_ERR.format(app=app, url=url))
    except Exception:
        logger.warning(MSG_EXTERNAL_APP_SERVER_ERR.format(app=app, url=url))

    return False  # it's not possible to connect with server :(


def get_external_app_settings(app):
    config = settings.EXTERNAL_APPS[app]
    return config if not settings.TESTING else config['test']


def get_external_app_url(app, request=None):
    base_url = get_external_app_settings(app)['url']

    # if the current url refers to any of the gateway protected ones
    # it might happen that the external url has the realm as an option like
    # http://gateway-server/{realm}/app-id/
    # in that case we need to replace it with the current realm
    if settings.GATEWAY_ENABLED:
        realm = get_path_realm(request, default_realm=settings.GATEWAY_PUBLIC_REALM)
        # change "{realm}" argument with the current realm
        base_url = base_url.format(realm=realm)

    return base_url


def get_external_app_token(app):
    return get_external_app_settings(app)['token']
