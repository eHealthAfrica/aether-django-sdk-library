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

import django.db.models.deletion

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.MULTITENANCY_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MtInstance',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                    )),
                ('instance', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mt',
                    to=settings.MULTITENANCY_MODEL,
                    verbose_name='instance',
                    )),
                ('realm', models.TextField(verbose_name='realm')),
            ],
            options={
                'verbose_name': 'instance by realm',
                'verbose_name_plural': 'instances by realm',
                'ordering': ['instance'],
            },
        ),
        migrations.AddIndex(
            model_name='mtinstance',
            index=models.Index(fields=['realm'], name='multitenanc_realm_4d6500_idx'),
        ),
    ]
