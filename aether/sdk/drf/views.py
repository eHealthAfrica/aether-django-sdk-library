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

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import ugettext as _


class FilteredMixin(object):

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
        except Exception as e:  # pragma: no cover
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
