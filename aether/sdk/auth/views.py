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

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from aether.sdk.auth.utils import get_or_create_user


@api_view(['GET', 'POST'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAuthenticated])
def auth_token(request, *args, **kwargs):
    '''
    GET:
    Returns the user token if exists

    POST:
    If logged in user is not admin:
        Generates and returns an auth token for him/her.

    If logged in user is admin:
        Given a username (POST entry) generates an auth token for him/her.
        If the username does not belong to an existing user,
        it's going to be created with a long and random password.
    '''

    try:
        if request.method == 'GET':
            # return the own token
            token = Token.objects.filter(user=request.user)
            if token.exists():
                return Response({'token': token.first().key})
            return Response({'token': None})

        username = request.data.get('username', request.user.username)
        if not request.user.is_staff:
            # only admin user can create tokens for other users
            username = request.user.username
        user = get_or_create_user(request, username)

        # gets the user token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key})

    except Exception as e:
        return Response({'message': str(e)}, status=500)
