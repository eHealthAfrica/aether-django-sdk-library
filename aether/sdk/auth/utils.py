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

from django.contrib.auth import get_user_model

from aether.sdk.multitenancy.utils import get_current_realm, add_user_to_realm


UserModel = get_user_model()
user_objects = UserModel.objects


def get_or_create_user(request, username):
    # gets the existing user or creates a new one
    _username = parse_username(request, username)
    try:
        user = user_objects.get(username=_username)
    except UserModel.DoesNotExist:
        realm = get_current_realm(request)
        user = user_objects.create_user(
            username=_username,
            first_name=username,
            last_name=realm or '',
            password=user_objects.make_random_password(length=100),
        )
        # only add user if it doesn't exist.
        add_user_to_realm(request, user)

    return user


def parse_username(request, username):
    # the internal username prepends the realm name
    realm = get_current_realm(request)

    if realm and not username.startswith(f'{realm}__'):
        username = f'{realm}__{username}'
    return username


def unparse_username(request, username):
    # the internal username prepends the realm name
    realm = get_current_realm(request)

    if realm and username.startswith(f'{realm}__'):
        username = username[len(f'{realm}__'):]
    return username


def user_to_string(user, request=None):
    '''
    Returns a readable name of the user.

    - ``first_name`` + ``last_name``
    - ``username``
    '''

    if user.first_name and user.last_name:
        return f'{user.first_name} {user.last_name}'

    if request:
        return unparse_username(request, user.username)
    return user.username
