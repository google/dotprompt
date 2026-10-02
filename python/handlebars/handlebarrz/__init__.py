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

"""Import name already-published dotpromptz 0.1.x uses.

`pip install dotpromptz==0.1.6` does `from handlebarrz import Handlebars`.
Remove this package once those releases no longer install this wheel
through `dotpromptz-handlebars>=0.1.8` with no upper bound.
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
