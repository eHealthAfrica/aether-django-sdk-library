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

'''
These urls are only used for testing purposes.
'''

from django.conf import settings
from django.conf.urls import include, url

from aether.sdk.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(
    token=settings.TEST_TOKEN_ACTIVE,
    app=[url(r'^test', include('aether.sdk.tests.fakeapp.urls'))],
)
