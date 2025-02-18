"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import Any, Dict, List, Union


def remove_undefined_fields(
    obj: Union[Dict[str, Any], List[Any], None],
) -> Union[Dict[str, Any], List[Any], None]:
    """
    Recursively removes None values from dictionaries, lists, and nested structures.
    """
    if obj is None or not isinstance(obj, (dict, list)):
        return obj

    if isinstance(obj, dict):
        return {
            k: remove_undefined_fields(v)
            for k, v in obj.items()
            if v is not None
        }

    if isinstance(obj, list):
        return [remove_undefined_fields(v) for v in obj if v is not None]

    return obj
