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

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from aether.sdk.utils import request
from aether.sdk.health.utils import get_external_app_url, get_external_app_token


class AppToken(models.Model):
    '''
    User authorization token to connect to the external application.
    '''

    user = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
    )

    app = models.TextField(
        help_text=_('This value corresponds to any of the ``settings.EXTERNAL_APPS`` values.'),
        verbose_name=_('application'),
    )

    token = models.CharField(
        blank=True,
        editable=False,
        help_text=_('This token corresponds to an authorization token linked to this user.'),
        max_length=40,
        null=True,
        verbose_name=_('token'),
    )

    @property
    def token_url(self):
        return get_external_app_url(self.app) + '/' + settings.TOKEN_URL

    def obtain_token(self):
        '''
        Gets the auth ``token`` from the app itself.
        '''

        if self.app not in settings.EXTERNAL_APPS:
            return None

        auxiliary_token = get_external_app_token(self.app)
        response = request(
            method='post',
            url=self.token_url,
            data={'username': self.user.username},
            headers={'Authorization': f'Token {auxiliary_token}'},
        )

        if response.status_code == 200:
            return response.json()['token']

        return None

    def validate_token(self):
        '''
        Checks if with the current auth ``token`` it's possible to connect to the app server.
        '''

        if self.app not in settings.EXTERNAL_APPS or self.token is None:
            return False

        response = request(
            method='get',
            url=self.token_url,
            headers={'Authorization': f'Token {self.token}'},
        )
        return response.status_code == 200

    @classmethod
    def get_or_create_token(cls, user, app_name):
        '''
        Gets the user auth token to connect to the app, checking first if it's valid.
        '''

        if app_name not in settings.EXTERNAL_APPS:
            return None

        app_token, _ = cls.objects.get_or_create(user=user, app=app_name)

        # if the current auth token is not valid then obtain a new one from app server
        if not app_token.validate_token():
            app_token.token = app_token.obtain_token()
            app_token.save()

        if app_token.token is None:
            return None

        return app_token

    class Meta:
        app_label = 'apptoken'
        default_related_name = 'app_tokens'
        verbose_name = _('application token')
        verbose_name_plural = _('application tokens')
        unique_together = ('user', 'app',)
