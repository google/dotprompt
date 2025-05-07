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

"""Pydantic model utilities."""

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel


def dump_models(items: Sequence[BaseModel] | None) -> list[dict[str, Any]]:
    """Dumps a list of Pydantic models to a list of dictionaries.

    Args:
        items: The list of Pydantic models to dump.

    Returns:
        A list of dictionaries.
    """
    if not items:
        return []
    return [item.model_dump(exclude_none=True, by_alias=True) for item in items]
