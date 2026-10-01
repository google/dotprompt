# handlebars-python

Renders the templates a Genkit prompt writes. The behavior is Handlebars 4.7.8. Where the Dart package disagrees with that, this package follows Handlebars.

```python
from handlebars import Handlebars

template = Handlebars().compile('Hello {{name}}!')
print(template({'name': 'World'}))
```

`{{name}}` reads the input. `{{@name}}` reads `data=`.

```python
template = Handlebars().compile('{{name}} {{@name}}')
print(template({'name': 'input'}, data={'name': 'context'}))
```

## What you can write

Variables: `{{name}}`, `{{user.name}}`, `{{user/name}}`, `{{a.[b c]}}`, `{{items.[0]}}`, `{{this.name}}`, `{{../name}}`. A list index is the bracket form. `{{items.0}}` is a broken template.

`{{{name}}}` and `{{&name}}` skip HTML escaping. Escaping is on by default and covers `& < > " ' ` =`.

Comments: `{{! ... }}` and `{{!-- ... --}}`. The long form can contain `}}`.

Blocks: `{{#if}}`, `{{#unless}}`, `{{#each}}`, `{{#with}}`, plus `{{else}}`, `{{else if}}`, and `{{else unless}}`. `{{#if n includeZero=true}}` treats 0 as yes.

`{{#name}}` and `{{^name}}` when `name` is data, not a helper. A list repeats. `{{^name}}` is the branch that runs when `{{#name}}` would not.

`{{#each items as |item index|}}` and `{{#with user as |u|}}` bind those names. Inside each, `{{.}}` is still the item. An outer name stays visible inside an inner each. `{{../name}}` is the parent value, not that name. `{{#user as |u|}}` does not bind `u`; `{{name}}` still reads the user.

Helpers, `key=value` arguments, and `(subexpressions)`. `{{"name"}}` calls a helper named `name`. With no such helper it prints nothing; it does not print the quotes' contents. `lookup` and `log` are built in. A helper that returns `SafeString` is inserted as written. `if`, `unless`, `each`, and `with` are built in and are not replaced by `register_helper`.

Partials: `{{> name}}`, `{{> name context key=value}}`, `{{> (which)}}` when `which` is a helper. `{{#> name}}default{{/name}}` uses the partial, or the default when it was never registered. The partial prints that default with `{{> @partial-block}}`. `{{#*inline "name"}}...{{/inline}}` defines a partial for the rest of that render.

Data: `{{@root}}`, `{{@index}}`, `{{@key}}`, `{{@first}}`, `{{@last}}`, `{{@../index}}`. On a list, `@key` is the index. On an object, `@key` is the key. Objects keep insertion order.

`~` removes the whitespace touching that side of a tag. A block, partial, or comment that is the only thing on its line does not leave the line behind. A partial called from an indented line indents its output to match.

`\{{` prints `{{`. `\\{{name}}` prints one backslash and then the value.

Numbers in a template are `1`, `-2`, and `1.5`. `.5` and `1e2` are not numbers.

## Which branch runs

| Value | `{{value}}` prints | `{{#if}}` | `{{#with}}` | `{{#each}}` | `{{#value}}` |
| --- | --- | --- | --- | --- | --- |
| missing or null | nothing | else | else | else | else |
| `false` | `false` | else | else | else | else |
| `0` | `0` | else (`includeZero=true` enters) | enters, and `{{.}}` is 0 | else | enters |
| `""` | nothing | else | else | else | enters |
| `[]` | nothing | else | else | else | else |
| `{}` | `[object Object]` | enters | enters | else | enters once |
| `[1, 2]` | `1,2` | enters | enters | once per item | once per item |
| `"ab"` | `ab` | enters | enters | else | enters once |

`{{#if}}` asks whether to show the branch. `{{#with}}` asks whether there is a value to step into. They disagree on `0`.

## Strict mode

`Handlebars(strict=True)` raises `StrictModeError` when the template prints a missing path, or uses one as `{{#name}}`. The error's `path` is that path. A missing path passed to `if`, `unless`, `each`, `with`, or a helper does not raise. It counts as empty. A key that is present and null does not raise.

## Partials and `@root`

`{{> missing}}` raises. `{{#> missing}}default{{/missing}}` prints `default`.

A partial starts a new context. `{{../name}}` inside it does not see the caller. `{{@root}}` and `{{@index}}` do.

`{{@root}}` is the input. If the `data` dict already contains `root`, that value is `{{@root}}` instead. Dotprompt still refuses a context key named `root` when the template reads `@root`. That check stays in the prompt layer. This package does not do it.

## Refused on purpose

`{{* decorator}}` raises. Decorators are not part of a prompt.

`{{{{raw}}}}` outputs its content literally without parsing. In Handlebars, 4-brace blocks pass unparsed content to a helper (`options.fn()`). A built-in `raw` helper renders the literal body as a safe string, matching Dart and Handlebars.js when `raw` is registered.

A function stored in the input raises. Register it with `register_helper`. The input is data.

A broken template raises `ValueError`. The wording is ours. What raises, and what renders, matches Handlebars 4.7.8.

## Why this cut

A prompt needs variables, `if` / `each` / `with`, helpers, partials, and `@root` / `@index`. The rows above are the cases a prompt author actually hits, including the ones that look like they should agree and do not.

The Dart library is the other pure implementation on the team, and its feature list is wider than its tests. A missing partial prints nothing there. `{{#with ""}}` enters. Those are not Handlebars. This package does not copy them.
