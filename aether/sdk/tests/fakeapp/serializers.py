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

from django.contrib.auth import get_user_model
from rest_framework import serializers

from aether.sdk.drf.serializers import (
    DynamicFieldsSerializer,
    DynamicFieldsModelSerializer,
    FilteredHyperlinkedRelatedField,
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
    UsernameField,
    UserNameField,
)
from aether.sdk.multitenancy.serializers import (
    MtModelSerializer,
    MtPrimaryKeyRelatedField,
    MtUserRelatedField,
)

from aether.sdk.tests.fakeapp.models import (
    TestModel,
    TestChildModel,
)

UserModel = get_user_model()


class TestModelSerializer(MtModelSerializer):

    url = HyperlinkedIdentityField(view_name='testmodel-detail')
    children_url = FilteredHyperlinkedRelatedField(
        view_name='testchildmodel-list',
        lookup_field='parent',
        read_only=True,
        source='children',
    )

    user = MtUserRelatedField(
        allow_null=True,
        default=None,
        queryset=UserModel.objects.all(),
    )
    uname = UserNameField(source='user')

    class Meta:
        model = TestModel
        fields = '__all__'


class TestChildModelSerializer(DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='testchildmodel-detail')
    parent_url = HyperlinkedRelatedField(
        view_name='testmodel-detail',
        read_only=True,
        source='parent',
    )

    parent = MtPrimaryKeyRelatedField(
        queryset=TestModel.objects.all(),
    )

    class Meta:
        model = TestChildModel
        fields = '__all__'


class TestUserSerializer(DynamicFieldsModelSerializer):

    username = UsernameField()

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email',)


class TestUserSerializer2(DynamicFieldsModelSerializer):

    name = UserNameField(source='*')

    class Meta:
        model = UserModel
        fields = (
            'id', 'username',
            # required to test UserNameField
            'name', 'first_name', 'last_name',
        )


class TestUserSerializer3(DynamicFieldsSerializer):

    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    def create(self, validated_data):
        return UserModel(**validated_data)
