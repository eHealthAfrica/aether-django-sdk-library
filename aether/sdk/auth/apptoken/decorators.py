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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import gettext_lazy as _

from aether.sdk.auth.apptoken.models import AppToken

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)

ERR_MSG_APP_TOKEN = _('Could not check the authorization token for "{user}" in "{app}".')


def app_token_required(*args, **kwargs):
    return login_required(_token_required(*args, **kwargs))


def _token_required(function=None, redirect_field_name=None, login_url=None):
    '''
    Decorator for views that checks that a user is logged in and
    has valid tokens for each app used in the proxy token view.
    '''

    def user_token_test(user):
        '''
        Checks for each external app that the user can currently connect to it.
        '''

        try:
            for app in settings.EXTERNAL_APPS:
                # checks if there is a valid token for this app
                if AppToken.get_or_create_token(user, app) is None:
                    logger.error(ERR_MSG_APP_TOKEN.format(user=user, app=app))
                    return False
            return True
        except Exception:
            return False

    actual_decorator = user_passes_test(
        test_func=lambda u: user_token_test(u),
        login_url=login_url or f'/{settings.CHECK_TOKEN_URL}',
        redirect_field_name=redirect_field_name,
    )
    return actual_decorator(function) if function else actual_decorator
