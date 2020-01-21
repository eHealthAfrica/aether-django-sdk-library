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
from django.db import transaction
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from aether.sdk.cache import clear_cache


class CacheViewSetMixin(object):
    '''
    Invalidates cache after any successful edit action.
    '''

    # the list of models to remove from cache every time an instance is updated
    cache_models = []
    # purges cache every time an instance is updated?
    cache_purge = False

    def finalize_response(self, request, response, *args, **kwargs):
        resp = super(CacheViewSetMixin, self).finalize_response(request, response, *args, **kwargs)
        if not settings.DJANGO_USE_CACHE:
            return resp

        # prevent browser cache
        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'    # HTTP 1.1.
        resp['Pragma'] = 'no-cache'                                      # HTTP 1.0.
        resp['Expires'] = '0'                                            # Proxies.

        if resp.status_code < 400 and request.method not in SAFE_METHODS:
            # invalidate cache after any successful edit action
            clear_cache(models=self.cache_models, purge=self.cache_purge)

        return resp


class FilteredMixin(CacheViewSetMixin):

    @transaction.atomic
    @action(detail=False, methods=['delete'], url_path='filtered-delete')
    def filtered_delete(self, request, *args, **kwargs):
        '''
        This adds a bulk delete action based on the supplied filters to a viewset
        accessible via:

        `/{modelname}/filtered-delete/?{query_string}`

        All delete operations are rolled back if any error is encountered
        '''
        try:
            filtered_list = self.filter_queryset(self.queryset)
            filtered_list.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    @action(detail=False, methods=['patch'], url_path='filtered-partial-update')
    def filtered_partial_update(self, request, *args, **kwargs):
        '''
        This adds a bulk update action based on the supplied filters to a viewset
        accessible via:

        `/{modelname}/filtered-partial-update/?{query_string}`

        the fields to be updated are passed in the body of the request as follows:

        `
        {
            'modelField1': 'new value',
            'modelField2': 'new value 1'
        }
        `

        all records that meet the filter criteria will have the specified fields
        updated to the corresponding values.

        All update operations are rolled back if any error is encountered

        '''
        if request.data:
            try:
                filtered_list = self.filter_queryset(self.queryset)
                for record in filtered_list:
                    serializer = self.get_serializer(record, data=request.data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
                return Response({'updated': filtered_list.count()}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    str(e),
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                _('No values to update'),
                status=status.HTTP_400_BAD_REQUEST
            )
