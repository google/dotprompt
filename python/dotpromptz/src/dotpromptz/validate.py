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

"""Output schema validation for rendered prompts.

Validates rendered prompt output against the JSON Schema defined in the
prompt's output configuration. Uses the ``jsonschema`` library for
Draft 2020-12 compliant validation.

Example::

    from dotpromptz.validate import validate_output

    schema = {
        'type': 'object',
        'properties': {'name': {'type': 'string'}},
        'required': ['name'],
    }
    validate_output({'name': 'Alice'}, schema)  # OK
    validate_output({'name': 123}, schema)  # Raises SchemaValidationError
"""

from __future__ import annotations

from typing import Any

import jsonschema
import structlog

from dotpromptz.typing import JsonSchema

logger = structlog.get_logger(__name__)


class SchemaValidationError(Exception):
    """Raised when output data fails validation against the output JSON Schema."""

    def __init__(self, message: str, errors: list[str]) -> None:
        """Initialize with a message and list of validation error strings.

        Args:
            message: A summary message.
            errors: Individual validation error descriptions.
        """
        super().__init__(message)
        self.errors = errors


def validate_output(data: Any, schema: JsonSchema) -> None:
    """Validate data against a JSON Schema.

    Args:
        data: The data to validate.
        schema: The JSON Schema to validate against.

    Raises:
        SchemaValidationError: If validation fails.
    """
    validator_cls = jsonschema.Draft202012Validator
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

    if errors:
        descriptions = [_format_error(e) for e in errors]
        raise SchemaValidationError(
            f'Output schema validation failed with {len(errors)} error(s): {"; ".join(descriptions)}',
            descriptions,
        )


def _format_error(error: jsonschema.ValidationError) -> str:
    """Format a single validation error into a readable string.

    Args:
        error: The jsonschema validation error.

    Returns:
        A human-readable error description.
    """
    path = '.'.join(str(p) for p in error.absolute_path) if error.absolute_path else '<root>'
    return f'{path}: {error.message}'
