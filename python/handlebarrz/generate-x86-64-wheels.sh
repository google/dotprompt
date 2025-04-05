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
export UV_LINK_MODE=copy

PYTHON_VERSION="python$1"

echo "building for python version $PYTHON_VERSION"

# linux
echo "building with maturin for linux"
for i in $(seq 40 -1 24); do
    uv run --python $1 maturin build --release --target x86_64-unknown-linux-gnu -i "$PYTHON_VERSION" --compatibility manylinux_2_$i --auditwheel=skip
done
uv run --python $1 maturin build --release --target x86_64-unknown-linux-gnu -i $PYTHON_VERSION

# windows 
echo "building with maturin for windows"
uv run --python $1 maturin  build --target x86_64-pc-windows-msvc -i $1

# macos
echo "building with maturin for macos"
uv run --python $1 maturin build --target x86_64-apple-darwin -i $1 --zig

DIRECTORY="target/wheels/"

FILES=$(find "$DIRECTORY" -type f -name "*linux_x86_64*")
if [ -n "$FILES" ]; then 
    echo "removing local wheel"
    rm -f $FILES
fi

