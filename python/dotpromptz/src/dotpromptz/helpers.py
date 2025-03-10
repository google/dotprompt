import json
from collections.abc import Callable
from typing import Any

from handlebars import Handlebars  # type: ignore

RenderCallable = Callable[[str], str]
HelperCallable = Callable[[Any, RenderCallable, int | None], str]


def register_helpers(env: Handlebars) -> None:
    """Register all dotprompt helpers with the Handlebars environment."""
    env.register_helper('json', json_helper)
    env.register_helper('role', role_helper)
    env.register_helper('history', history_helper)
    env.register_helper('section', section_helper)
    env.register_helper('media', media_helper)
    env.register_helper('ifEquals', if_equals_helper)
    env.register_helper('unlessEquals', unless_equals_helper)


def json_helper(
    text: str, render: RenderCallable, indent: int | None = None
) -> str:
    """Serialize a value to JSON with optional indentation."""
    try:
        value = json.loads(text)
        return (
            json.dumps(value, indent=indent)
            if isinstance(indent, int)
            else json.dumps(value)
        )
    except Exception as e:
        return f'Error serializing JSON: {e}'


def role_helper(text: str, render: RenderCallable) -> str:
    """Generate a role marker."""
    return f'<<{text}>>'


# helpers.py
def history_helper(text: str, render: RenderCallable) -> str:
    """Generate a history marker."""
    return f'<<history>>{text}<</history>>'  # Changed from <>{text}<>


def section_helper(name: str, render: RenderCallable) -> str:
    """Generate a section marker."""
    return f'<<section {name}>>'  # Added name parameter


def media_helper(text: str, render: RenderCallable) -> str:
    """Generate a media marker."""
    parts = text.split()
    url = parts[0]
    content_type = parts[1] if len(parts) > 1 else None
    if content_type is not None:
        return f'<<media url="{url}" type="{content_type}" >>'  # Fixed format
    return f'<<media url="{url}" >>'


def if_equals_helper(arg1: str, arg2: str, options: dict[str, Any]) -> str:
    """Compare two values and render the block if they are equal."""
    if arg1 == arg2:
        return str(options['fn'](this=None))  # Explicit cast to str
    else:
        return str(options['inverse'](this=None))  # Explicit cast to str


def unless_equals_helper(arg1: str, arg2: str, options: dict[str, Any]) -> str:
    """Compare two values and render the block if they are not equal."""
    if arg1 != arg2:
        return str(options['fn'](this=None))  # Explicit cast to str
    else:
        return str(options['inverse'](this=None))  # Explicit cast to str
