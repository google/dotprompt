# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

from dotpromptz.dotprompt import Dotprompt


def package_name() -> str:
    return 'dotpromptz'


__all__ = [
    'Dotprompt',
    'package_name',
]
