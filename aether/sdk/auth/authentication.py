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

from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed

from aether.sdk.auth.utils import parse_username
from aether.sdk.multitenancy.utils import check_user_in_realm


class GatewayBasicAuthentication(BasicAuthentication):
    '''
    Extends DRF Basic Authentication prepending the realm to the given username.
    '''

    def authenticate_credentials(self, userid, password, request=None):
        userid = parse_username(request, userid)

        user = super(GatewayBasicAuthentication, self) \
            .authenticate_credentials(userid, password, request)[0]

        # check that the user belongs to the current realm
        if not check_user_in_realm(request, user):
            raise AuthenticationFailed(_('Invalid user in this realm.'))

        return (user, None)
