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

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import action, api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from aether.sdk.drf.views import CacheViewSetMixin
from aether.sdk.multitenancy.utils import (
    filter_by_realm,
    filter_users_by_realm,
    is_accessible_by_realm,
)


class MtViewSetMixin(CacheViewSetMixin):
    '''
    Defines ``get_queryset`` method to filter by realm.

    Expects ``mt_field`` property.

    Adds two new methods:
        - ``get_object_or_404(pk)`` raises NOT_FOUND error if the instance
          does not exists or is not accessible by current realm.
        - ``get_object_or_403(pk)`` raises FORBIDDEN error if the instance
          exists and is not accessible by current realm.

    Adds a detail endpoint ``/is-accessible`` only permitted with HEAD method,
    returns the following statuses:
        - 403 FORBIDDEN   if the instance is not accessible by current realm
        - 404 NOT_FOUND   if the instance does not exist
        - 204 NO_CONTENT  otherwise
    '''

    mt_field = None

    def get_queryset(self):
        '''
        Includes filter by realm in each query
        '''

        qs = super(MtViewSetMixin, self).get_queryset()
        return filter_by_realm(self.request, qs, self.mt_field)

    def get_object_or_404(self, pk):
        '''
        Custom method that raises NOT_FOUND error
        if the instance does not exists or is not accessible by current realm
        otherwise return the instance
        '''

        return get_object_or_404(self.get_queryset(), pk=pk)

    def get_object_or_403(self, pk):
        '''
        Custom method that raises FORBIDDEN error
        if the instance exists and is not accessible by current realm
        otherwise returns the instance or ``None`` if it does not exist
        '''

        # without filtering by realm
        qs = super(MtViewSetMixin, self).get_queryset()
        if not qs.filter(pk=pk).exists():
            return None

        obj = qs.get(pk=pk)
        if not is_accessible_by_realm(self.request, obj):
            raise PermissionDenied(_('Not accessible by this realm'))

        return obj

    @action(detail=True, methods=['head'], url_path='is-accessible')
    def is_accessible(self, request, pk=None, *args, **kwargs):
        '''
        Returns the following statuses:
            - 404 NOT_FOUND   if the instance does not exist
            - 403 FORBIDDEN   if the instance is not accessible by current realm
            - 204 NO_CONTENT  otherwise
        '''

        self.get_object_or_403(pk)
        self.get_object_or_404(pk)

        return Response(status=204)


class MtUserViewSetMixin(CacheViewSetMixin):
    '''
    Defines ``get_queryset`` method to filter by realm authorization group.
    '''

    def get_queryset(self):
        '''
        Includes filter by realm authorization group in each query
        '''

        qs = super(MtUserViewSetMixin, self).get_queryset()
        return filter_users_by_realm(self.request, qs)


@api_view(['GET'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAdminUser])
def get_realms(*args, **kwargs):
    '''
    Get the list of current realms.

    If MULTITENANCY is not enabled then
    returns the fake realm `settings.NO_MULTITENANCY_REALM`

    If MULTITENANCY is enabled then
    the default realm is always included in the list
    '''
    if settings.MULTITENANCY:
        from aether.sdk.multitenancy.models import MtInstance
        realms = set(
            MtInstance.objects.values_list('realm', flat=True).order_by('realm').distinct()
        )
        # include always the default realm
        realms.add(settings.DEFAULT_REALM)

    else:
        realms = [settings.NO_MULTITENANCY_REALM]

    return Response({'realms': list(realms)})
