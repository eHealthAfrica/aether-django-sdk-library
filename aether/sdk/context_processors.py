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
from aether.sdk.multitenancy.utils import get_path_realm


def eha_context(request):

    context = {
        'dev_mode': settings.DEBUG,

        'app_name': settings.APP_NAME,
        'app_name_html': settings.APP_NAME_HTML,
        'app_link': settings.APP_LINK,

        'app_favicon': settings.APP_FAVICON,
        'app_logo': settings.APP_LOGO,

        'app_version': settings.VERSION,
        'app_revision': settings.REVISION,

        'app_extra_style': settings.APP_EXTRA_STYLE,
        'app_extra_meta': settings.APP_EXTRA_META,

        'app_url': settings.APP_URL,
    }

    if settings.GATEWAY_ENABLED:
        realm = get_path_realm(request)
        if realm:
            context['app_url'] = f'/{realm}/{settings.GATEWAY_SERVICE_ID}'

    return context
