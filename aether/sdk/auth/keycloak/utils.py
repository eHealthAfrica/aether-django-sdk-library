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

import urllib.parse

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.middleware.csrf import CSRF_SESSION_KEY
from django.urls import reverse

from aether.sdk.auth.utils import get_or_create_user
from aether.sdk.cache import cache_wrap
from aether.sdk.multitenancy.utils import get_current_realm
from aether.sdk.utils import find_in_request_headers, request as exec_request


_KC_TOKEN_SESSION = '__keycloak__token__session__'
_KC_URL = settings.KEYCLOAK_SERVER_URL
_KC_OID_URL = 'protocol/openid-connect'


def get_realm_auth_url(request):
    realm = get_current_realm(request, default_realm=None)
    redirect_uri = urllib.parse.quote(_get_login_url(request), safe='')

    return (
        f'{_KC_URL}/{realm}/{_KC_OID_URL}/auth?'
        f'&client_id={settings.KEYCLOAK_CLIENT_ID}'
        '&scope=openid'
        '&response_type=code'
        f'&redirect_uri={redirect_uri}'
    )


def check_realm(realm):
    '''
    Checks if the realm name is valid visiting its keycloak server login page.
    '''

    response = exec_request(method='head', url=f'{_KC_URL}/{realm}/account')
    response.raise_for_status()


def authenticate(request, username, password, realm):
    '''
    Logs in in the keycloak server with the given username, password and realm.
    '''

    try:
        # get user token+info
        token, userinfo = _authenticate(
            realm=realm,
            data={
                'grant_type': 'password',
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'username': username,
                'password': password,
            })
    except Exception:
        return None

    # save the current realm in the session
    request.session[settings.REALM_COOKIE] = realm
    # save the user token in the session
    request.session[_KC_TOKEN_SESSION] = token
    request.session.modified = True

    return _get_or_create_user(request, userinfo)


def post_authenticate(request):
    session_state = request.GET.get('session_state')
    code = request.GET.get('code')
    realm = get_current_realm(request, default_realm=None)

    if not session_state or not code or not realm:
        return

    redirect_uri = _get_login_url(request)
    token, userinfo = _authenticate(
        realm=realm,
        data={
            'grant_type': 'authorization_code',
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_session_state': session_state,
            'client_session_host': redirect_uri,
            'code': code,
            'redirect_uri': redirect_uri,
        })

    # save the user token in the session
    request.session[_KC_TOKEN_SESSION] = token
    request.session.modified = True

    return _get_or_create_user(request, userinfo)


def check_user_token(request):
    '''
    Checks if the user token is valid refreshing it in keycloak server.
    '''

    token = request.session.get(_KC_TOKEN_SESSION)
    realm = get_current_realm(request, default_realm=None)
    if token and realm:
        # refresh token
        response = refresh_kc_token(realm, token)
        try:
            response.raise_for_status()
            request.session[_KC_TOKEN_SESSION] = response.json()
            request.session.modified = True
        except Exception:
            logout(request)


# memoize (realm token pairs for TTL set by USER_TOKEN_TTL)
# TTL must be longer than Token validity
@cache_wrap(timeout=settings.USER_TOKEN_TTL)
def refresh_kc_token(realm, token):
    return exec_request(
        method='post',
        url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/token',
        data={
            'grant_type': 'refresh_token',
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'refresh_token': token['refresh_token'],
        },
    )


def check_gateway_token(request):
    '''
    Checks if the gateway token is valid fetching the user info from keycloak server.
    '''

    token = find_in_request_headers(request, settings.GATEWAY_HEADER_TOKEN)
    realm = get_current_realm(request, default_realm=None)
    if token and realm:
        try:
            userinfo = _get_user_info(realm, token)

            # flags that we are using the gateway to authenticate
            request.session[settings.GATEWAY_HEADER_TOKEN] = True
            request.session[settings.REALM_COOKIE] = realm
            request.session.modified = True

            user = _get_or_create_user(request, userinfo)
            # only login if the user changed otherwise it will refresh the Csrf
            # token and make the AJAX calls fail.
            if not hasattr(request, 'user') or request.user.pk != user.pk:
                login(request, user)

                # WORKAROUND!!!
                # Using curl behind the gateway always returns CSRF errors due
                # to the missing CSRF Token in the request headers.
                # We are adding it manually to skip this issue but
                # only if it needs to login
                csrfCookie = request.META.get('CSRF_COOKIE')
                if not request.META.get(settings.CSRF_HEADER_NAME):
                    request.META[settings.CSRF_HEADER_NAME] = csrfCookie
                if not request.session.get(CSRF_SESSION_KEY):
                    request.session[CSRF_SESSION_KEY] = csrfCookie
            request.user = user

        except Exception:
            # something went wrong
            logout(request)

    elif request.session.get(settings.GATEWAY_HEADER_TOKEN):
        # this session was using the gateway to authenticate before
        logout(request)


@receiver(user_logged_out)
def _user_logged_out(sender, user, request, **kwargs):
    '''
    Removes realm and token from session also logs out from keycloak server
    making the user token invalid.
    '''

    token = request.session.get(_KC_TOKEN_SESSION)
    realm = get_current_realm(request, default_realm=None)
    if token and realm:
        # logout
        exec_request(
            method='post',
            url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/logout',
            data={
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'refresh_token': token['refresh_token'],
            },
        )


def _get_login_url(request):
    return request.build_absolute_uri(reverse('rest_framework:login'))


def _authenticate(realm, data):
    # get user token from the returned "code"
    response = exec_request(
        method='post',
        url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/token',
        data=data,
    )
    response.raise_for_status()

    token = response.json()
    userinfo = _get_user_info(realm, token['access_token'])
    return token, userinfo


@cache_wrap(timeout=settings.USER_TOKEN_TTL)
def _get_user_info(realm, token):
    response = exec_request(
        method='get',
        url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/userinfo',
        headers={'Authorization': f'Bearer {token}'},
    )
    response.raise_for_status()

    return response.json()


def _get_or_create_user(request, userinfo):
    user = get_or_create_user(request, userinfo.get('preferred_username'))
    update_user = False
    demographic_pairs = [
        ('first_name', 'given_name'),
        ('last_name', 'family_name'),
        ('email', 'email')
    ]
    for k_user, k_userinfo in demographic_pairs:
        v_user = getattr(user, k_user)
        v_userinfo = userinfo.get(k_userinfo, '')
        if v_user != v_userinfo:
            setattr(user, k_user, v_userinfo)
            update_user = True
    if update_user:
        user.save()

    return user
