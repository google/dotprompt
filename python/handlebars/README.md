# handlebars-dotprompt

A pure-Python Handlebars implementation, owned by the Genkit team. It implements the subset of Handlebars that [Dotprompt](https://github.com/google/dotprompt) templates use, not the full language.

Dotprompt is language-agnostic. A `.prompt` file should render the same way in every SDK, so what a prompt does is defined by the file, not by the language running it. To keep that true, this package treats Handlebars.js 4.7.9 as the spec. Handlebars has no standalone spec. Handlebars.js is the reference implementation that the other ports follow, so where implementations disagree, Handlebars.js wins. 4.7.9 is the latest Handlebars.js release, and it's what the Dotprompt JS SDK's `^4.7.8` range resolves to on a fresh install. Conformance tests check this package's output against it.

No Rust or Node at runtime.

```
uv add handlebars-dotprompt
```

## Quick start

```python
from handlebars_dotprompt import Handlebars

# 1. Compile once
hb = Handlebars()
render = hb.compile(
    'Table for {{party}}. '
    '{{#if allergies}}Avoid: {{#each allergies}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}.{{/if}}'
)

# 2. Render many times
print(render({'party': 4, 'allergies': ['peanuts', 'shellfish']}))
# => Table for 4. Avoid: peanuts, shellfish.

print(render({'party': 2, 'allergies': []}))
# => Table for 2.
```

`compile()` returns a function. Call it with your input dict. Pass `data=` for values the template reads with `@`:

```python
render = hb.compile('{{name}} / {{@request_id}}')
print(render({'name': 'Ana'}, data={'request_id': 'r-42'}))
# => Ana / r-42
```

## Helpers

A helper is `fn(args, options)`. `args` holds the positional arguments and `options.hash` holds the `key=value` ones.

```python
def price(args, options):
    cents = args[0]
    currency = options.hash.get('currency', 'USD')
    return f'{cents / 100:.2f} {currency}'


hb.register_helper('price', price)
print(hb.compile('Salmon: {{price cents currency="EUR"}}')({'cents': 1850}))
# => Salmon: 18.50 EUR
```

For a block helper (`{{#name}}...{{/name}}`), `options.fn(context)` renders the body and `options.inverse(context)` renders the `{{else}}` body:

```python
def loud(args, options):
    return options.fn(options.context).upper()


hb.register_helper('loud', loud)
print(hb.compile('{{#loud}}chef says {{dish}}{{/loud}}')({'dish': 'tartine'}))
# => CHEF SAYS TARTINE
```

Helper output gets escaped like any other value. Return a `SafeString` to insert markup as written. Escaping is then up to you.

`if`, `unless`, `each`, `with`, `lookup`, and `log` are built in. You can't override them with `register_helper`.

## Partials

```python
hb.register_partial('dish', '- {{name}} ({{price}})\n')
render = hb.compile('Menu:\n{{#each dishes}}{{> dish}}{{/each}}')
print(render({'dishes': [{'name': 'Tartine', 'price': 14}, {'name': 'Soup', 'price': 9}]}))
# => Menu:
#    - Tartine (14)
#    - Soup (9)
```

A missing partial raises. `{{#> name}}fallback{{/name}}` renders the fallback instead. Inline partials (`{{#*inline "name"}}`) and dynamic partials (`{{> (helperName)}}`) work too.

## Escaping

`{{value}}` HTML-escapes by default. `{{{value}}}` doesn't.

```python
render = Handlebars().compile('{{note}} | {{{note}}}')
print(render({'note': 'Fish & <b>Chips</b>'}))
# => Fish &amp; &lt;b&gt;Chips&lt;/b&gt; | Fish & <b>Chips</b>
```

Prompts usually go to a model, not a browser. To turn escaping off everywhere, use `Handlebars(escape_html=False)`.

## Strict mode

`Handlebars(strict=True)` raises when the template prints a path that isn't in the input:

```python
from handlebars_dotprompt import Handlebars, StrictModeError

try:
    Handlebars(strict=True).compile('Hello {{user.name}}')({'user': {}})
except StrictModeError as err:
    print(err.path)
# => user.name
```

Conditions don't raise. `{{#if user.name}}` on a missing path takes the else branch.

## Values that surprise Python developers

Dotprompt defines what a template means, independent of the language that renders it. Dotprompt templates use Handlebars semantics, and this package takes them from Handlebars.js 4.7.9. Conditionals and printed values follow those semantics, not Python's `bool()` or `str()`:

- `0` fails `{{#if}}` but enters `{{#with}}`. Use `{{#if n includeZero=true}}` to keep `0`.
- `{}` enters `{{#if}}`. `{{#if}}` takes the else branch only for a missing key, `None`, `False`, `""`, `0`, or `[]`.
- Lists print as `1,2` and dicts print as `[object Object]`. Format structured data with a helper. Dotprompt ships `{{json value}}` for this.
- `1.0` prints as `1`, and `False` prints as `false`.

## What's not supported

These raise `ValueError`:

- Decorators (`{{* name}}`).
- Functions in the input dict. Register them with `register_helper`, so a template can only call code you chose.
- Broken templates. Which templates fail matches Handlebars.js, but the error messages are worded differently.

Everything else a prompt uses is supported:
- **Paths:** `user.name`, `../name`, `items.[0]`
- **Blocks:** `if`, `unless`, `each`, `with`, with `else` and `else if`
- **Block parameters:** `as |item index|`
- **Data:** `@index`, `@key`, `@first`, `@last`, `@root`
- **Syntax:** subexpressions, comments, `~` whitespace control, and raw blocks (`{{{{raw}}}}`)
