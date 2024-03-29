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

from django.contrib.auth.forms import AuthenticationForm
from django.forms import Form, CharField, TextInput, ValidationError
from django.utils.translation import gettext_lazy as _

from aether.sdk.auth.keycloak.utils import authenticate, check_realm


class RealmMixin(object):

    def clean_realm(self):
        '''
        Checks that the realm exists in keycloak server.
        '''

        try:
            realm = self.cleaned_data.get('realm')
            check_realm(realm)
            return realm
        except Exception:
            raise ValidationError(_('Invalid realm'))


class RealmForm(Form, RealmMixin):

    realm = CharField(label=_('Realm'), strip=True, widget=TextInput(attrs={'autofocus': True}))

    def __init__(self, request=None, *args, **kwargs):
        '''
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        '''

        self.request = request

        super().__init__(*args, **kwargs)


class RealmAuthenticationForm(AuthenticationForm, RealmMixin):
    '''
    Extends Authentication form adding the "realm" field.
    '''

    realm = CharField(label=_('Realm'), strip=True, widget=TextInput)

    def clean(self):
        '''
        Authenticates against keycloak server.
        '''

        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        realm = self.cleaned_data.get('realm')

        if username and password and realm:
            self.user_cache = authenticate(self.request, username, password, realm)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
