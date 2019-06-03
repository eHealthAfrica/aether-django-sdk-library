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

from django.contrib import admin

from aether.sdk.auth.cas.models import UserRole


class UserRoleAdmin(admin.ModelAdmin):

    list_display = ('name', 'user', 'group',)

    show_full_result_count = True
    empty_value_display = '---'
    list_per_page = 25


admin.site.register(UserRole, UserRoleAdmin)
