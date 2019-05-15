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
from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.Model):

    name = models.TextField(verbose_name=_('name'))

    # the matching group for this role
    group = models.ForeignKey(to=Group,
                              null=True,
                              blank=True,
                              on_delete=models.CASCADE,
                              verbose_name=_('group'))

    # the user
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                             null=True,
                             blank=True,
                             on_delete=models.CASCADE,
                             verbose_name=_('user'))

    def __str__(self):  # pragma: no cover
        return f'{self.user.username} - {self.name}'

    class Meta:
        app_label = 'cas'
        ordering = ['name']
        unique_together = ('user', 'group')

        verbose_name = 'user role'
        verbose_name_plural = 'user roles'
        default_related_name = 'user_roles'
