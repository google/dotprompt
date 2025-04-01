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

. /venv/bin/activate
echo "building for python version $1"

# linux
echo "building with maturin for linux"
for i in $(seq 40 -1 24); do
    maturin build --release --target x86_64-unknown-linux-gnu -i "$1" --compatibility manylinux_2_$i --auditwheel=skip
done
maturin build --release --target x86_64-unknown-linux-gnu -i $1

# for glibc > 2.28
# maturin build --release --target x86_64-unknown-linux-gnu -i python3.12 --compatibility manylinux_2_40 --auditwheel=skip

# windows 
echo "building with maturin for windows"
maturin  build --target x86_64-pc-windows-msvc -i $1

# macos
echo "building with maturin for macos"
maturin build --target x86_64-apple-darwin -i $1 --zig

