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

"""Errors for the dotpromptz package."""


class ResolverFailedError(RuntimeError):
    """Raised when a resolver fails."""

    def __init__(self, name: str, kind: str, reason: str) -> None:
        """Initialize the error.

        Args:
            name: The name of the object that failed to resolve.
            kind: The kind of object that failed to resolve.
            reason: The reason the object resolver failed.
        """
        self.name = name
        self.kind = kind
        self.reason = reason
        super().__init__(f'{kind} resolver failed for {name}; {reason}')

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return f'{self.kind} resolver failed for {self.name}; {self.reason}'

    def __repr__(self) -> str:
        """Return a string representation of the error."""
        return f'{self.kind} resolver failed for {self.name}; {self.reason}'
