# handlebars-python

A pure Python implementation of the Handlebars template engine.

```python
from handlebars import Handlebars

template = Handlebars().compile('Hello {{name}}!')
print(template({'name': 'World'}))
```

`{{@name}}` reads the `data` dict, not the input dict.

```python
template = Handlebars().compile('{{name}} {{@name}}')
print(template({'name': 'input'}, data={'name': 'context'}))
```

HTML escaping is on by default. `Handlebars(escape_html=False)`, `{{{name}}}`, and `{{&name}}` leave markup as written.

A missing variable renders as nothing. `Handlebars(strict=True)` raises `StrictModeError` and the message names the path.
