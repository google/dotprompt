# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Typed shim for the js2py Handlebars transpiled implementation."""

from __future__ import annotations

from ._safe_string import SafeString
from ._shim import Handlebars

__all__ = ['Handlebars', 'SafeString']
