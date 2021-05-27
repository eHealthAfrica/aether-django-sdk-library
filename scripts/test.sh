#!/usr/bin/env bash
#
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
#
set -Eeuo pipefail

# ----------------------------------------
# remove previous results
# ----------------------------------------
coverage erase || true

# ----------------------------------------
# set up test environment
# ----------------------------------------

# copy VERSION and REVISION in temporal files
mkdir -p /var/tmp
echo "1.2.3"   > /var/tmp/VERSION
echo "testing" > /var/tmp/REVISION


# ----------------------------------------
# lint tests
# ----------------------------------------
flake8

# ----------------------------------------
# unit tests
# ----------------------------------------
coverage run \
    --concurrency=multiprocessing \
    --parallel-mode \
    test.py test --parallel --noinput "${@:1}"

coverage combine --append

# ----------------------------------------
# print results
# ----------------------------------------
coverage report

# ----------------------------------------
# cleaning
# ----------------------------------------
coverage erase
rm -f /var/tmp/VERSION
rm -f /var/tmp/REVISION
