#!/usr/bin/env python

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

import os
import sys

if __name__ == '__main__':
    from django.core.management import execute_from_command_line

    # take all testing environment variables from file
    with open('./scripts/test.ini') as envfile:
        for line in envfile:
            if line.strip() and not line.startswith('#'):
                setting = line.strip().split('=', maxsplit=1)
                os.environ.setdefault(setting[0], setting[1])

    execute_from_command_line(sys.argv)
