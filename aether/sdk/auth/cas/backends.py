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

from django_cas_ng.backends import CASBackend

# to store the roles on successful callback
from django_eha_sdk.auth.cas.callbacks import setup_callbacks

setup_callbacks()


class CASRoleBackend(CASBackend):
    '''
    CAS role to group permission adapter
    '''

    def get_group_permissions(self, user_obj, obj=None):
        '''
        Returns a set of permission strings the user ``user_obj`` has from the
        groups they belong by role assignment from CAS server.
        '''

        # the resulting permission set for the roles
        result = set()

        for user_role in user_obj.userrole_set.all():
            if user_role.group:
                for permission in user_role.group.permissions.all():
                    permission_name = '{1}.{0}'.format(*permission.natural_key()[:2])
                    result.add(permission_name)

        return result

    def has_perm(self, user, perm, obj):
        permissions = self.get_group_permissions(user, obj)
        return perm in permissions
