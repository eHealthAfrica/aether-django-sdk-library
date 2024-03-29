# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from aether.sdk.auth.keycloak.forms import RealmForm
from aether.sdk.auth.keycloak.utils import post_authenticate, get_realm_auth_url


class KeycloakLoginView(LoginView):
    '''
    Executes Login process in three steps:

    1.- Displays the realm form. (GET)
    2.- Checks the realm and redirects to keycloak server to continue login. (POST)
    3.- Receives keycloak response and finalize authentication process. (GET)
    '''

    template_name = settings.DEFAULT_KEYCLOAK_TEMPLATE
    authentication_form = RealmForm

    def get(self, request, *args, **kwargs):
        try:
            user = post_authenticate(request)
            if user:
                auth_login(request, user)
                return HttpResponseRedirect(self.get_success_url())
        except Exception:
            # remove realm
            request.session[settings.REALM_COOKIE] = None
            request.session.modified = True
            messages.error(request, _('An error ocurred while authenticating against keycloak'))

        return super(KeycloakLoginView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        # save the current realm in the session
        self.request.session[settings.REALM_COOKIE] = form.cleaned_data.get('realm')
        self.request.session.modified = True
        # redirect to keycloak
        return HttpResponseRedirect(get_realm_auth_url(self.request))


class KeycloakLogoutView(LogoutView):
    '''
    Extends LogoutView overriding ``get_next_page`` method.

    In case of Gateway Authentication is enabled and the next page refers to the
    Gateway urls redirect to Gateway logout endpoint.
    '''

    def get_next_page(self):
        next_page = super(KeycloakLogoutView, self).get_next_page()
        try:
            # remove query string or "resolve" method will fail
            page = urllib.parse.unquote(next_page).split('?')[0]
            realm = resolve(page).kwargs.get('realm')
            if realm and realm != settings.GATEWAY_PUBLIC_REALM:
                url = f'/{realm}/{settings.GATEWAY_SERVICE_ID}/logout'
                return self.request.build_absolute_uri(url)
        except Exception:
            # sometimes there is no next_page or resolve fails...
            pass

        return next_page
