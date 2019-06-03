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
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.views import View

from aether.sdk.auth.apptoken.models import AppToken
from aether.sdk.health.utils import get_external_app_url
from aether.sdk.multitenancy.utils import (
    add_current_realm_in_headers,
    get_path_realm,
)
from aether.sdk.utils import (
    request as exec_request,
    get_meta_http_name,
    normalize_meta_http_name,
)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)

ERR_MSG_APP_UNKNOWN = _('"{}" app is not recognized.')
ERR_MSG_NO_TOKEN = _('User "{}" cannot connect to app "{}"')


@login_required()
def user_app_token_view(request, *args, **kwargs):
    return render(request, 'eha/tokens.html', {
        'user_app_tokens': AppToken.objects.filter(user=request.user),
    })


class TokenProxyView(View):
    '''
    This view will proxy any request to the indicated app with
    the user auth token or the Gateway token.
    '''

    app_name = None
    '''
    The app that the proxy should forward requests to.
    '''

    def dispatch(self, request, path='', *args, **kwargs):
        '''
        Dispatches the request adding/modifying the needed properties
        '''

        if self.app_name not in settings.EXTERNAL_APPS:
            err = ERR_MSG_APP_UNKNOWN.format(self.app_name)
            logger.error(err)
            raise RuntimeError(err)

        # if the current url refers to any of the gateway protected ones
        # instead of using the App User Token we rely security in the Gateway
        needs_token = True
        if settings.GATEWAY_ENABLED:
            realm = get_path_realm(request, default_realm=settings.GATEWAY_PUBLIC_REALM)
            # needs user token if url refers to the public realm
            needs_token = (realm == settings.GATEWAY_PUBLIC_REALM)

        if needs_token:
            app_token = AppToken.get_or_create_token(request.user, self.app_name)
            if app_token is None:
                err = ERR_MSG_NO_TOKEN.format(request.user, self.app_name)
                logger.error(err)
                raise RuntimeError(err)
            request.META[get_meta_http_name('authorization')] = f'Token {app_token.token}'

        _path = path or ''
        if not _path.startswith('/'):
            _path = '/' + _path

        # build request path info with `base_url` + `path` + `query string`
        base_url = get_external_app_url(self.app_name, request)
        query_string = request.GET.urlencode()
        url = f'{base_url}{_path}' + (f'?{query_string}' if query_string else '')
        request.external_url = url

        return super(TokenProxyView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self._handle(request)

    def get(self, request, *args, **kwargs):
        return self._handle(request)

    def head(self, request, *args, **kwargs):
        return self._handle(request)

    def options(self, request, *args, **kwargs):
        return self._handle(request)

    def patch(self, request, *args, **kwargs):
        return self._handle(request)

    def post(self, request, *args, **kwargs):
        return self._handle(request)

    def put(self, request, *args, **kwargs):
        return self._handle(request)

    def _handle(self, request):
        def _valid_header(name):
            '''
            Validates if the header can be passed within the request headers.
            '''

            # bugfix: We need to remove the "Host" from the header
            # since the request goes to another host, otherwise
            # the webserver returns a 404 because the domain is
            # not hosted on that server. The webserver
            # should add the correct Host based on the request.
            # This problem might not be exposed running on localhost

            return (
                name in ['CONTENT_TYPE'] or
                (name.startswith('CSRF_') and name not in ['CSRF_COOKIE_USED']) or
                (name.startswith('HTTP_') and name not in ['HTTP_HOST'])
            )

        def _get_method(request):
            # Fixes:
            # django.http.request.RawPostDataException:
            #     You cannot access body after reading from request's data stream
            #
            # Django does not read twice the `request.body` on `POST` calls:
            # but it was already read while checking the CSRF token.
            # This raises an exception in the line below `data=request.body ...`.
            # The Ajax call changed it from `POST` to `PUT`,
            # here it's changed back to its real value.
            #
            # All the conditions are checked to avoid further issues with this workaround.
            if request.method == 'PUT' and request.META.get('HTTP_X_METHOD', '').upper() == 'POST':
                return 'POST'
            return request.method

        # builds request headers
        headers = {
            normalize_meta_http_name(header): str(value)
            for header, value in request.META.items()
            if _valid_header(header)
        }
        headers = add_current_realm_in_headers(request, headers)

        method = _get_method(request)
        logger.debug(f'{method}  {request.external_url}')
        response = exec_request(method=method,
                                url=request.external_url,
                                data=request.body if request.body else None,
                                headers=headers,
                                )
        if response.status_code == 204:  # NO-CONTENT
            http_response = HttpResponse(status=response.status_code)
        else:
            http_response = HttpResponse(
                content=response,
                status=response.status_code,
                content_type=response.headers.get('Content-Type'),
            )

        # copy the exposed headers from the original response ones
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Expose-Headers
        # https://fetch.spec.whatwg.org/#http-access-control-expose-headers
        expose_headers = response.headers.get('Access-Control-Expose-Headers', '').split(', ')
        for key in expose_headers:
            if key in response.headers:
                http_response[key] = response.headers[key]
        return http_response
