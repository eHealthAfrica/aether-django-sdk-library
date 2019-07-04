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
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppToken',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                    )),
                ('app', models.TextField(
                    help_text=(
                        'This value corresponds to any of the ``settings.EXTERNAL_APPS`` values.'
                    ),
                    verbose_name='application',
                    )),
                ('token', models.CharField(
                    blank=True,
                    editable=False,
                    help_text=(
                        'This token corresponds to an authorization token linked to this user.'
                    ),
                    max_length=40,
                    null=True,
                    verbose_name='token',
                    )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='app_tokens',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='user',
                    )),
            ],
            options={
                'verbose_name': 'application token',
                'verbose_name_plural': 'application tokens',
                'default_related_name': 'app_tokens',
                'unique_together': {('user', 'app')},
            },
        ),
    ]
