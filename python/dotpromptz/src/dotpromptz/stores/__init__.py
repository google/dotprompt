# Copyright 2026 Google LLC
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

"""Deprecated import path.

`genkit<=0.12.0` on PyPI depends on `dotpromptz>=0.1.5` without an upper bound
and imports `from dotpromptz.stores import ...`. This shim keeps those legacy
installations working.

Remove this shim in `dotpromptz>=0.3.0` after `genkit<=0.12.0` has aged out
and users have upgraded.
"""

from dotpromptz._stores._dir_async import DirStore
from dotpromptz._stores._dir_sync import DirStoreSync
from dotpromptz._stores._typing import DirStoreOptions

__all__ = ['DirStore', 'DirStoreOptions', 'DirStoreSync']
