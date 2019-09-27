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
        qs = super(FilteredMixin, self).get_queryset()
        filter_class = self.filter_class
        try:
            filtered_list = filter_class(self.request.GET, queryset=qs)
            filtered_list.qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:  # pragma: no cover
            return Response(
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    @action(detail=False, methods=['patch'], url_path='filtered-update')
    def filtered_update(self, request, *args, **kwargs):
        if request.data:
            qs = super(FilteredMixin, self).get_queryset()
            filter_class = self.filter_class
            try:
                filtered_list = filter_class(self.request.GET, queryset=qs)
                for record in filtered_list.qs:
                    for field in request.data:
                        setattr(record, field, request.data[field])
                    # use individual save to trigger pre and post save events
                    record.save()
                return Response({'updated': filtered_list.qs.count()}, status=status.HTTP_200_OK)
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
