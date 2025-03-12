import json as json_lib
from typing import Any, Dict
import handlebars

hb = handlebars.Handlebars()

@hb.helper('json')
def json(serializable: Any, options: Dict) -> str:
    indent = options.get('hash', {}).get('indent', 0)
    return json_lib.dumps(serializable, indent=indent)

@hb.helper('role')
def role(role: str) -> str:
    return f"<<<dotprompt:role:{role}>>>"

@hb.helper('history')
def history() -> str:
    return "<<<dotprompt:history>>>"

@hb.helper('section')
def section(name: str) -> str:
    return f"<<<dotprompt:section {name}>>>"

@hb.helper('media')
def media(context: Any, options: Dict) -> str:
    url = options.get('hash', {}).get('url', '')
    content_type = options.get('hash', {}).get('contentType', '')
    return f"<<<dotprompt:media:url {url}{' ' + content_type if content_type else ''}>>"

@hb.helper('ifEquals')
def ifEquals(this: Any, arg1: Any, arg2: Any, options: Dict) -> str:
    return options['fn'](this) if arg1 == arg2 else options['inverse'](this)

@hb.helper('unlessEquals')
def unlessEquals(this: Any, arg1: Any, arg2: Any, options: Dict) -> str:
    return options['fn'](this) if arg1 != arg2 else options['inverse'](this)
