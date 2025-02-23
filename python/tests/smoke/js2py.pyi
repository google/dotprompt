# js2py.pyi

from typing import Any

class EvalJs:
    def __init__(
        self, context: dict[str, Any] = {}, enable_require: bool = False
    ) -> None: ...
    def execute(self, js_code: str) -> None: ...
    def __getattr__(self, name: str) -> Any:
        """Dynamically access JavaScript functions/variables."""
        pass
