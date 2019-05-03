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
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _

from django_eha_sdk.health.utils import check_db_connection, check_external_app

BAD_RESPONSE = _('Always Look on the Bright Side of Life!!!')
OK_RESPONSE = _('Brought to you by eHealth Africa - good tech for hard places')


def health(*args, **kwargs):
    '''
    Simple view to check if the system is up.
    '''

    return HttpResponse(status=200)


def check_db(*args, **kwargs):
    '''
    Health check for the default DB connection.
    '''

    if not check_db_connection():
        return HttpResponse(BAD_RESPONSE, status=500)

    return HttpResponse(OK_RESPONSE)


def check_app(*args, **kwargs):
    '''
    Health check for the current app version and more.
    '''

    return JsonResponse({
        'app_name': settings.APP_NAME,
        'app_version': settings.VERSION,
        'app_revision': settings.REVISION,
    })


def check_external(*args, **kwargs):
    '''
    Check if the connection with external server is possible
    '''

    app_name = kwargs.get('name')

    if not check_external_app(app_name):
        return HttpResponse(BAD_RESPONSE, status=500)
    return HttpResponse(OK_RESPONSE)
