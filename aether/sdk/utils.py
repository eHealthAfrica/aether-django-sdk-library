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

import json
import os
import requests

from time import sleep

from django.conf import settings
from django.http import FileResponse
from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer


def __prettified__(response, lexer):
    # Truncate the data. Alter as needed
    response = response[:settings.PRETTIFIED_CUTOFF]
    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')
    # Highlight the data
    response = highlight(response, lexer, formatter)
    # Get the stylesheet
    style = '<style>' + formatter.get_style_defs() + '</style>'
    # Safe the output
    return mark_safe(style + response)


def json_prettified(value, indent=2):
    '''
    Function to display pretty version of our json data
    https://www.pydanny.com/pretty-formatting-json-django-admin.html
    '''
    return __prettified__(json.dumps(value, indent=indent), JsonLexer())


def get_meta_http_name(name):
    return 'HTTP_' + name.replace('-', '_').upper()  # HTTP_<KEY>,


def normalize_meta_http_name(name):
    return name.replace('HTTP_', '').title().replace('_', '-')


def find_in_request(request, key, default_value=None):
    '''
    Finds the key in
        - the request session or
        - within the request cookies or
        - within the request headers.

    https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest.COOKIES
    '''

    return getattr(request, 'session', {}).get(
        key,
        getattr(request, 'COOKIES', {}).get(
            key,
            find_in_request_headers(request, key, default_value)
        )
    )


def find_in_request_headers(request, key, default_value=None):
    '''
    Finds the key within the request headers.

    https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest.META

    New in Django.2.2
    https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest.headers
    '''

    return getattr(request, 'headers', {}).get(  # New in Django 2.2
        key,
        getattr(request, 'META', {}).get(
            get_meta_http_name(key),
            default_value
        )
    )


def request(*args, **kwargs):
    '''
    Executes the request call at least X times (``REQUEST_ERROR_RETRIES``)
    trying to avoid unexpected connection errors (not request expected ones).

    Like:

        # ConnectionResetError: [Errno 104] Connection reset by peer
        # http.client.RemoteDisconnected: Remote end closed connection without response
    '''

    count = 0
    while True:
        count += 1
        try:
            return requests.request(*args, **kwargs)
        except Exception as e:
            if count >= settings.REQUEST_ERROR_RETRIES:
                raise e
        sleep(count)  # sleep longer in each iteration


def get_all_docs(url, **kwargs):
    '''
    Returns all documents linked to an url, even with pagination
    '''

    def _get_data(url):
        resp = request(method='get', url=url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    data = {'next': url}
    while data.get('next'):
        data = _get_data(data['next'])
        for x in data['results']:
            yield x


def get_file_content(file_name, file_url, as_attachment=False):
    '''
    Gets file content usually from File Storage URL and returns it back.
    '''

    try:
        # Remote server
        response = request(method='get', url=file_url, stream=True)
    except requests.exceptions.MissingSchema:
        # File system
        response = open(os.path.abspath(file_url), 'rb')

    filename = file_name.split('/')[-1] if file_name else file_url.split('/')[-1]
    http_response = FileResponse(
        streaming_content=response,
        as_attachment=as_attachment,
        # take the last part of the filename path
        filename=filename,
        status=getattr(response, 'status_code', None),
        content_type=getattr(response, 'headers', {}).get('Content-Type'),
    )
    http_response.set_headers(filelike=response)

    if as_attachment:
        http_response['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return http_response
