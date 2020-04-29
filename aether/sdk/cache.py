# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
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
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.timezone import now

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


# Content type values should never change
# Use this as an in-memory cache
CONTENT_TYPE_CACHE = {}


def _is_cacheops_enabled():
    return settings.DJANGO_USE_CACHE and 'cacheops' in settings.INSTALLED_APPS


def cache_wrap(timeout=settings.CACHE_TTL):
    if _is_cacheops_enabled():
        from cacheops import cached
        return cached(timeout=timeout)

    # put a fake cache function on global scope so it doesn't complain
    def do_nothing(fn):
        return fn

    return do_nothing


def get_content_type(model):
    try:
        return CONTENT_TYPE_CACHE[model]
    except KeyError:
        try:
            CONTENT_TYPE_CACHE[model] = ContentType.objects.get_for_model(model)
            return CONTENT_TYPE_CACHE[model]
        except Exception:
            pass

    return None


def clear_cache(objects=None, models=None, purge=False):
    # this is required to refresh the templates content
    # otherwise after any update the page will not refresh properly
    try:
        cache.clear()
    except Exception as e:
        # ignore errors
        logger.error(str(e))

    if _is_cacheops_enabled():
        from cacheops import invalidate_all, invalidate_model, invalidate_obj

        if objects:
            for obj in objects:
                invalidate_obj(obj)

        if models:
            for model in models:
                get_content_type(model=model)  # add it to the models list
                invalidate_model(model)

        if purge:
            try:
                invalidate_all()
            except Exception as e:
                # Fixes: unknown command `FLUSHDB`
                #   In helm charts FLUSHDB and FLUSHALL commands are disabled
                logger.error(str(e))
                clear_cache(models=list(CONTENT_TYPE_CACHE.keys()))


@staff_member_required
def purge_view(*args, **kwargs):
    '''
    Simple view to invalidate cache
    '''

    clear_cache(purge=True)

    return JsonResponse(data={'time': now()})
