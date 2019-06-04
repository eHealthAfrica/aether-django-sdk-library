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

import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from django_cas_ng.signals import cas_user_authenticated

from aether.sdk.auth.cas.models import UserRole

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


def set_user_roles(user, roles):
    # remove existing assignments in DB
    UserRole.objects.filter(user=user).delete()

    # create new assignments
    for role_name in roles:
        # try to find matching Group
        user_role = UserRole(name=role_name, user=user)
        try:
            group = Group.objects.get(name__iexact=role_name)
            user_role.group = group
        except Group.DoesNotExist:
            logger.warning(_('local Group with name "{}" does not exist').format(role_name))

        user_role.save()


def auth_callback(sender, user=None, attributes=None, **kwargs):
    if user and attributes:
        roles = attributes.get('roles') or ''
        set_user_roles(user, roles.split(','))

        # also update first name and last name if empty
        if not user.first_name.strip():
            # update the user object with information given from the response
            user.first_name = attributes.get('first_name')
            user.last_name = attributes.get('last_name')
            user.email = attributes.get('email', '')
            user_img = attributes.get('user_image', '')

            if hasattr(user, 'profile') and user.profile:
                # use attached profile object to store additional data if present
                user.profile.profile_picture_url = user_img
                user.profile.display_name = attributes.get('display_name', '')
                user.profile.save()

            # do something with user image here ..
            user.save()


def setup_callbacks():
    cas_user_authenticated.connect(auth_callback)
