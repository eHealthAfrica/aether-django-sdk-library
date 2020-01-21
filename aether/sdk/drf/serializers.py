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

import urllib

from rest_framework import serializers
from rest_framework.reverse import reverse

from aether.sdk.auth.utils import parse_username, unparse_username, user_to_string
from aether.sdk.multitenancy.utils import get_path_realm


def custom_reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    if not kwargs:
        kwargs = {}

    realm = get_path_realm(request)
    if realm:
        kwargs['realm'] = realm

    return reverse(viewname=viewname,
                   args=args,
                   kwargs=kwargs,
                   request=request,
                   format=format,
                   **extra)


class HyperlinkedRelatedField(serializers.HyperlinkedRelatedField):

    def __init__(self, view_name=None, **kwargs):
        super(HyperlinkedRelatedField, self).__init__(view_name, **kwargs)

        # override the reverse method used internally
        self.reverse = custom_reverse


class HyperlinkedIdentityField(serializers.HyperlinkedIdentityField, HyperlinkedRelatedField):
    pass


class FilteredHyperlinkedRelatedField(HyperlinkedRelatedField):
    '''
    This custom field does essentially the same thing as
    ``serializers.HyperlinkedRelatedField``.

    The only difference is that the url of a foreign key relationship will be:

        {
            ...
            'children_url': '/children?parent=<parent-id>'
            ...
        }

    Instead of:

        {
            ...
            'children_url': '/parent/<parent-id>/children/'
            ...
        }

    '''

    def get_url(self, obj, view_name, request, format):
        lookup_field_value = obj.instance.pk
        result = '{}?{}'.format(
            self.reverse(view_name, kwargs={}, request=request, format=format),
            urllib.parse.urlencode({self.lookup_field: lookup_field_value})
        )
        return result


# https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
class DynamicFieldsSerializerMixin(object):
    '''
    Add additional functionality to Serializers adding two arguments ``fields`` and ``omit``
    that control which fields should be displayed.
    '''
    def __init__(self, *args, **kwargs):
        # Don't pass the custom arguments up to the superclass
        fields = kwargs.pop('fields', None)
        omit = kwargs.pop('omit', None)

        # Instantiate the superclass normally
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the ``fields`` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if omit:
            # Drop any fields that are specified in the ``omit`` argument.
            not_allowed = set(omit)
            for field_name in not_allowed:
                self.fields.pop(field_name, None)


class DynamicFieldsSerializer(DynamicFieldsSerializerMixin, serializers.Serializer):
    pass


class DynamicFieldsModelSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    pass


class UsernameField(serializers.Field):
    '''
    Custom serializer for username fields.

    The internal value is the username with the "realm" (parsed).
    The displayed value is the username without the "realm" (unparsed).
    '''

    def to_representation(self, value):
        return unparse_username(self.context['request'], value)

    def to_internal_value(self, data):
        return parse_username(self.context['request'], data)


class UserNameField(serializers.ReadOnlyField, serializers.RelatedField):
    '''
    Custom serializer to display user's full name.
    '''

    def to_representation(self, value):
        return user_to_string(value, self.context['request'])
