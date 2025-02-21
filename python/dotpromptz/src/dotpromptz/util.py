# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for dotpromptz."""

from collections.abc import Mapping, Sequence
from typing import Any


def remove_undefined_fields(obj: Any) -> Any:
    """Remove undefined fields from an object recursively.

    Args:
        obj: Object to process.

    Returns:
        Object with undefined fields removed.
    """
    if obj is None or not isinstance(obj, Mapping | Sequence):
        return obj

    if isinstance(obj, Sequence) and not isinstance(obj, str | bytes):
        return [
            remove_undefined_fields(item) for item in obj if item is not None
        ]

    if isinstance(obj, Mapping):
        return {
            key: remove_undefined_fields(value)
            for key, value in obj.items()
            if value is not None
        }

    return obj
