#!/usr/bin/env bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

set -eu

python_version=$1
candidate_index=$2
package_version=$3
target=$4

# Resolver configuration from the runner must not influence provenance.
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL PIP_FIND_LINKS PIP_NO_INDEX
unset UV_INDEX UV_INDEX_URL UV_DEFAULT_INDEX UV_EXTRA_INDEX_URL UV_FIND_LINKS UV_NO_INDEX
export PIP_CONFIG_FILE=/dev/null
export UV_NO_CONFIG=1

echo "Executing for Python $python_version from $candidate_index"
ldd --version

uv python install "$python_version"
rm -rf .smoke-venv
uv venv .smoke-venv --python "$python_version"
uv pip install \
  --python .smoke-venv \
  --no-cache \
  --index-url "https://pypi.org/simple" \
  --only-binary=:all: \
  "packaging>=24.2" \
  "pip>=24" \
  "structlog>=25.2.0"
rm -rf candidate-download
mkdir candidate-download
.smoke-venv/bin/python -m pip download \
  --isolated \
  --no-cache-dir \
  --index-url "$candidate_index" \
  --only-binary=:all: \
  --no-deps \
  --dest candidate-download \
  "dotpromptz-handlebars==$package_version"
set -- candidate-download/*.whl
[ "$#" -eq 1 ]
wheel=$1
.smoke-venv/bin/python release_verifier.py verify-smoke-wheel \
  --candidate candidate \
  --wheel "$wheel" \
  --target "$target" \
  --version "$package_version"
uv pip install \
  --python .smoke-venv \
  --no-cache \
  --no-build \
  --no-deps \
  "$wheel"
.smoke-venv/bin/python handlebarrz_test.py

