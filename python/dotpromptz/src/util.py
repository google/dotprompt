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


from typing import Any
def remove_undefined_fields(
    obj: None | dict[str, Any] | list[Any] | str | int | float | bool
) -> None | dict[str, Any] | list[Any] | str | int | float | bool:
    '''Recursively removes None values from dictionaries, lists, and nested structures.'''
    if obj is None:
        return None
    
    if isinstance(obj, dict):
        return {
            key: cleaned
            for key, value in obj.items()
            if (cleaned := remove_undefined_fields(value)) is not None
        }
    
    if isinstance(obj, list):
        return [
            cleaned
            for item in obj
            if (cleaned := remove_undefined_fields(item)) is not None
        ]
    
    return obj
