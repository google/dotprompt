#!/bin/bash
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


# git clone git@github.com:google/dotprompt.git
# cd js
# pnpm i
# pnpm build
# pnpm test

# pnpm login --registry https://wombat-dressing-room.appspot.com

CURRENT=`pwd`
RELEASE_BRANCH="${RELEASE_BRANCH:-main}"
RELEASE_TAG="${RELEASE_TAG:-next}"

cd js
pnpm publish --tag $RELEASE_TAG --publish-branch $RELEASE_BRANCH --registry https://wombat-dressing-room.appspot.com
