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

"""Compatibility shim for already-published dotpromptz 0.1.x releases.

`dotpromptz==0.1.6` on PyPI depends on `dotpromptz-handlebars>=0.1.8` without
an upper bound and imports `from handlebarrz import Handlebars`. This shim keeps
those legacy installations working.

Remove this shim in a future stable release (e.g. 1.0.0) after users have had
sufficient time to upgrade to `dotpromptz>=0.2.0`.
"""

from dotpromptz_handlebars import *  # noqa: F403
from dotpromptz_handlebars import (
    Context as Context,
    EscapeFunction as EscapeFunction,
    Handlebars as Handlebars,
    HelperFn as HelperFn,
    HelperOptions as HelperOptions,
    RuntimeOptions as RuntimeOptions,
)
