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

from django.utils.translation import gettext_lazy as _

from rest_framework.authentication import (
    BasicAuthentication as BasicAuth,
    TokenAuthentication as TokenAuth,
)
from rest_framework.exceptions import AuthenticationFailed

from aether.sdk.auth.utils import parse_username
from aether.sdk.multitenancy.utils import check_user_in_realm, get_current_realm


class BasicAuthentication(BasicAuth):
    '''
    Extends DRF Basic Authentication prepending the realm to the given username.
    '''

    def authenticate_credentials(self, userid, password, request=None):
        try:
            user, __ = super(BasicAuthentication, self) \
                .authenticate_credentials(userid, password, request)

        except AuthenticationFailed:
            userid = parse_username(request, userid)
            user, __ = super(BasicAuthentication, self) \
                .authenticate_credentials(userid, password, request)

        # check that the user belongs to the current realm
        if not check_user_in_realm(request, user):
            raise AuthenticationFailed(_('Invalid user in this realm.'))

        return (user, None)

    def authenticate_header(self, request):
        realm = get_current_realm(request) or self.www_authenticate_realm
        return f'Basic realm="{realm}"'


class TokenAuthentication(TokenAuth):
    '''
    Extends DRF Token Authentication checking that the user belongs to the realm.
    '''

    def authenticate(self, request):
        response = super(TokenAuthentication, self).authenticate(request)
        if response is None:
            return response

        # check that the user belongs to the current realm
        if not check_user_in_realm(request, response[0]):
            raise AuthenticationFailed(_('Invalid user in this realm.'))

        return response
