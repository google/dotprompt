# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

# js2py.pyi
from collections.abc import Callable
from typing import Any

class EvalJs:
    def __init__(
        self, context: dict[str, Any] = {}, enable_require: bool = False
    ) -> None: ...
    def execute(self, js_code: str) -> None: ...
    def __getattr__(self, name: str) -> Any:
        """Dynamically access JavaScript functions/variables."""
        pass

def eval_js(js_code: str) -> Callable[..., Any]: ...

class Function:
    def __call__(self, *args: Any) -> Any: ...
