# Copyright 2026 Google LLC
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

"""Turn a template into pieces, then render the pieces.

Text stays text. {{name}} looks up a value. {{#if}} owns a body and an else
body. ~ on a tag removes the whitespace touching that tag.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, cast

from dotpromptz_handlebars._types import (
    Block,
    ElseNode,
    HelperFn,
    InlinePartial,
    Mustache,
    Node,
    Options,
    Partial,
    PartialBlock,
    SafeString,
    TagToken,
    TemplateRecursionError,
    Text,
)

_MAX_DEPTH = 100


class _Unbound:
    """A block param named on {{#yes as |name|}}. That branch never assigns it."""


_MISSING = object()


class StrictModeError(Exception):
    """Raised when a path is missing and strict mode is on."""

    path: str

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f'{path} is not defined')


class Rendered(str):
    """Text that already went through the template, so it is not escaped again."""


def compile_template(source: str, max_depth: int = _MAX_DEPTH) -> list[Node]:
    """Parses a template into nodes. Raises ValueError when a tag is unclosed."""
    return _parse(_tokens(source), max_depth=max_depth)


def render_program(
    program: list[Node],
    context: Any,
    *,
    data: dict[str, Any] | None,
    helpers: dict[str, HelperFn],
    partials: dict[str, Any],
    escape_html: bool,
    strict: bool,
    reserved_data_keys: Iterable[str] | None = None,
    max_depth: int = _MAX_DEPTH,
) -> str:
    """Renders parsed nodes. data is the dict {{@name}} reads.

    @root is the input. A data dict that already contains root replaces it.
    """
    frame: dict[str, Any] = {'root': context, **(data or {})}
    return _render(
        program,
        scopes=[context],
        blocks=[{}],
        frames=[frame],
        helpers=helpers,
        partials=dict(partials),
        escape_html=escape_html,
        strict=strict,
        reserved_data_keys=set(reserved_data_keys) if reserved_data_keys else None,
        raw_data=data or {},
        depth=0,
        max_depth=max_depth,
    )


def _tokens(source: str) -> list[TagToken | str]:
    parts: list[TagToken | str] = []
    i = 0
    n = len(source)
    while i < n:
        start = source.find('{{', i)
        if start < 0:
            parts.append(source[i:])
            break
        slashes = 0
        j = start - 1
        while j >= i and source[j] == '\\':
            slashes += 1
            j -= 1
        if slashes == 1:
            # A single backslash is the only escape. \{{ is the two characters {{.
            parts.append(source[i : start - 1] + '{{')
            i = start + 2
            continue
        if slashes >= 2:
            # \\{{ is one backslash and a real tag. \\\{{ is two, and a real tag.
            parts.append(source[i : start - slashes] + ('\\' * (slashes - 1)))
        elif start > i:
            parts.append(source[i:start])
        if source.startswith('{{{{', start):
            if source.startswith('{{{{/', start):
                raise ValueError('unexpected closing tag')
            open_end = source.find('}}}}', start + 4)
            if open_end < 0:
                raise ValueError('unclosed tag')
            header = source[start + 4 : open_end].strip()
            if not header:
                raise ValueError('empty tag')
            raw_name = header.split()[0]
            close_tag = '{{{{/' + raw_name + '}}}}'
            content_start = open_end + 4
            close_pos = source.find(close_tag, content_start)
            if close_pos < 0:
                raise ValueError(f'unclosed raw block {raw_name}')
            raw_content = source[content_start:close_pos]
            parts.append(TagToken(body=f'#{header}', raw_block=True))
            if raw_content:
                parts.append(raw_content)
            parts.append(TagToken(body=f'/{raw_name}', raw_block=True))
            i = close_pos + len(close_tag)
            continue
        long_end = _long_comment_end(source, start)
        if long_end is not None:
            end, closer = long_end
            body = source[start + closer : end]
            strip_before = body.startswith('~')
            strip_after = body.endswith('~')
            body = body[1:] if strip_before else body
            body = body[:-1] if strip_after else body
            parts.append(TagToken(body=body.strip(), strip_before=strip_before, strip_after=strip_after))
            i = end + closer
            continue

        if source.startswith('{{~{', start):
            body_start = start + 4
            strip_before = True
            triple = True
        elif source.startswith('{{{', start):
            body_start = start + 3
            strip_before = False
            triple = True
        else:
            body_start = -1
            strip_before = False
            triple = False

        if triple:
            p1 = source.find('}}}', body_start)
            p2 = source.find('}~}}', body_start)
            if p1 >= 0 and p2 >= 0:
                if p1 < p2:
                    end = p1
                    closer = 3
                    strip_after = False
                else:
                    end = p2
                    closer = 4
                    strip_after = True
            elif p1 >= 0:
                end = p1
                closer = 3
                strip_after = False
            elif p2 >= 0:
                end = p2
                closer = 4
                strip_after = True
            else:
                raise ValueError('unclosed tag')
            body = source[body_start:end]
            parts.append(TagToken(body=body.strip(), triple=True, strip_before=strip_before, strip_after=strip_after))
            i = end + closer
            continue

        end = source.find('}}', start + 2)
        closer = 2
        if end < 0:
            raise ValueError('unclosed tag')
        body = source[start + closer : end]
        strip_before = body.startswith('~')
        strip_after = body.endswith('~')
        body = body[1:] if strip_before else body
        body = body[:-1] if strip_after else body
        parts.append(TagToken(body=body.strip(), triple=False, strip_before=strip_before, strip_after=strip_after))
        i = end + closer
    return _drop_standalone_lines(_strip_neighbors(parts))


def _long_comment_end(source: str, start: int) -> tuple[int, int] | None:
    """Index of }} for a {{!-- comment, or None when this tag is not one."""
    i = start + 2
    if i < len(source) and source[i] == '~':
        i += 1
    if not source.startswith('!--', i):
        return None
    search = i + 3
    while True:
        mark = source.find('--', search)
        if mark < 0:
            raise ValueError('unclosed tag')
        j = mark + 2
        if j < len(source) and source[j] == '~':
            j += 1
        if source.startswith('}}', j):
            return j, 2
        search = mark + 1


def _strip_neighbors(parts: list[TagToken | str]) -> list[TagToken | str]:
    for index, part in enumerate(parts):
        if not isinstance(part, TagToken):
            continue
        if part.strip_before and index and isinstance(parts[index - 1], str):
            prev = parts[index - 1]
            assert isinstance(prev, str)
            parts[index - 1] = prev.rstrip()
        if part.strip_after and index + 1 < len(parts) and isinstance(parts[index + 1], str):
            nxt = parts[index + 1]
            assert isinstance(nxt, str)
            parts[index + 1] = nxt.lstrip()
    return parts


def _drop_standalone_lines(parts: list[TagToken | str]) -> list[TagToken | str]:
    """A block, partial, or comment alone on a line does not leave that blank line.

    Which tags qualify is decided from the original line breaks. Dropping one
    tag's newline must not hide that the next tag is also alone on its line.
    """
    planned: list[tuple[int, int, str]] = []
    for index, part in enumerate(parts):
        if not isinstance(part, TagToken) or not _standalone_tag(part.body):
            continue
        if not _starts_line(parts, index):
            continue
        line_end = _line_ending_after(parts, index)
        if line_end is None:
            continue
        indent = _indent_before(parts, index) if part.body.startswith('>') else ''
        planned.append((index, line_end, indent))
    for index, line_end, indent in planned:
        _trim_indent_before(parts, index)
        part = parts[index]
        if isinstance(part, TagToken):
            part.indent = indent
        if line_end:
            nxt = parts[index + 1]
            if isinstance(nxt, str):
                parts[index + 1] = nxt[line_end:]
    return parts


def _starts_line(parts: list[TagToken | str], index: int) -> bool:
    """True when only spaces or tabs sit between this tag and the previous newline."""
    for cursor in range(index - 1, -1, -1):
        part = parts[cursor]
        if not isinstance(part, str):
            return False
        newline = part.rfind('\n')
        if newline >= 0:
            return not part[newline + 1 :].strip(' \t')
        if part.strip(' \t'):
            return False
    return True


def _line_ending_after(parts: list[TagToken | str], index: int) -> int | None:
    """How many characters of the following line ending to drop, or None."""
    if index + 1 >= len(parts):
        return 0
    nxt = parts[index + 1]
    if not isinstance(nxt, str):
        return None
    line_end = _standalone_line_end(nxt)
    if line_end is None:
        return None
    return len(line_end)


def _trim_indent_before(parts: list[TagToken | str], index: int) -> None:
    for cursor in range(index - 1, -1, -1):
        part = parts[cursor]
        if not isinstance(part, str):
            return
        newline = part.rfind('\n')
        if newline >= 0:
            parts[cursor] = part[: newline + 1]
            return
        parts[cursor] = ''


def _standalone_line_end(text: str) -> str | None:
    """The spaces and newline after a tag that sits at the end of its line."""
    index = 0
    while index < len(text) and text[index] in ' \t':
        index += 1
    if index == len(text):
        return text
    if text.startswith('\r\n', index):
        return text[: index + 2]
    if text.startswith('\n', index):
        return text[: index + 1]
    return None


def _indent_before(parts: list[TagToken | str], index: int) -> str:
    """Spaces on the partial's own line. They are copied onto each line it renders."""
    indent = ''
    for cursor in range(index - 1, -1, -1):
        part = parts[cursor]
        if not isinstance(part, str):
            return ''
        newline = part.rfind('\n')
        if newline >= 0:
            return part[newline + 1 :] + indent
        if part.strip(' \t'):
            return ''
        indent = part + indent
    return indent


def _standalone_tag(body: str) -> bool:
    if body.startswith(('!', '#', '/', '>', '^')):
        return True
    return body == 'else' or body.startswith('else ')


def _parse(parts: list[TagToken | str], max_depth: int = _MAX_DEPTH) -> list[Node]:
    nodes, index = _until(parts, 0, None, depth=0, max_depth=max_depth)
    if index != len(parts):
        raise ValueError('unexpected closing tag')
    return nodes


def _until(
    parts: list[TagToken | str],
    index: int,
    stop: str | None,
    depth: int = 0,
    max_depth: int = _MAX_DEPTH,
) -> tuple[list[Node], int]:
    if depth > max_depth:
        raise TemplateRecursionError(f'maximum template depth exceeded ({max_depth})')
    nodes: list[Node] = []
    while index < len(parts):
        part = parts[index]
        index += 1
        if isinstance(part, str):
            if part:
                nodes.append(Text(part))
            continue
        body = part.body
        triple = part.triple
        indent = part.indent
        if body.startswith('!'):
            continue
        if body.startswith('*'):
            raise ValueError('decorators are not supported')
        if body.startswith('/'):
            name = body[1:].split()[0]
            if stop != name:
                raise ValueError(f'unexpected closing tag {name}')
            return nodes, index
        if body == 'else' or body.startswith('else '):
            if stop is None:
                raise ValueError('{{else}} outside a block')
            inverse, index = _until(parts, index, stop, depth=depth + 1, max_depth=max_depth)
            if body.startswith('else if ') or body.startswith('else unless '):
                cond = body[len('else ') :]
                nested_body, nested_else = _split_else(inverse)
                inverse = cast(list[Node], [Block(_call(cond), nested_body, nested_else)])
            nodes.append(ElseNode(inverse))
            return nodes, index
        if body.startswith('#*inline'):
            name = _unquote(body.split(None, 2)[1])
            inner, index = _until(parts, index, 'inline', depth=depth + 1, max_depth=max_depth)
            nodes.append(InlinePartial(name, _without_else(inner)))
            continue
        if body.startswith('#>'):
            call = _call(body[2:].strip())
            inner, index = _until(parts, index, call['name'], depth=depth + 1, max_depth=max_depth)
            context_path = call['args'][0] if call['args'] else None
            nodes.append(PartialBlock(call['name'], _without_else(inner), context_path, call['hash']))
            continue
        if body.startswith('#') or body.startswith('^'):
            inverse_section = body.startswith('^')
            call = _call(body[1:])
            inner, index = _until(parts, index, call['name'], depth=depth + 1, max_depth=max_depth)
            body_nodes, inverse = _split_else(inner)
            if inverse_section:
                body_nodes, inverse = inverse, body_nodes
            if part.raw_block and call['name'] == 'raw' and not call['args'] and not call['hash']:
                nodes.extend(body_nodes)
                continue
            nodes.append(Block(call, body_nodes, inverse))
            continue
        if body.startswith('>'):
            call = _call(body[1:].strip())
            context_path = call['args'][0] if call['args'] else None
            nodes.append(Partial(call['name'], context_path, call['hash'], indent))
            continue
        src = body[1:].strip() if body.startswith('&') else body
        nodes.append(Mustache(_call(src), raw=triple or body.startswith('&')))
    if stop:
        raise ValueError('unclosed block')
    return nodes, index


def _split_else(nodes: list[Node]) -> tuple[list[Node], list[Node]]:
    if nodes and isinstance(nodes[-1], ElseNode):
        return nodes[:-1], nodes[-1].body
    return nodes, []


def _without_else(nodes: list[Node]) -> list[Node]:
    body, _ = _split_else(nodes)
    return body


def _call(header: str) -> dict[str, Any]:
    params: list[str] = []
    if ' as |' in header:
        header, rest = header.split(' as |', 1)
        params = rest.rstrip('|').split()
    bits = _args(header.strip())
    hashed: dict[str, str] = {}
    positional: list[str] = []
    for bit in bits:
        if '=' in bit and bit[0] not in '"\'(':
            key, value = bit.split('=', 1)
            if not key or not all(_id_char(char) for char in key):
                raise ValueError(f'{key} is not valid')
            _check_token(value)
            hashed[key] = value
        else:
            positional.append(bit)
    if not positional:
        raise ValueError('empty tag')
    raw_name = positional[0]
    literal = _is_quoted(raw_name)
    if literal:
        name = _unescape(raw_name)
    else:
        _check_token(raw_name)
        name = raw_name
    for bit in positional[1:]:
        _check_token(bit)
    return {'name': name, 'args': positional[1:], 'hash': hashed, 'params': params, 'literal': literal}


def _args(text: str) -> list[str]:
    bits: list[str] = []
    buf: list[str] = []
    depth = 0
    quote = ''
    for char in text:
        if quote:
            buf.append(char)
            if char == quote:
                quote = ''
            continue
        if char in '"\'':
            quote = char
            buf.append(char)
            continue
        if char in '([':
            depth += 1
        elif char in ')]':
            depth -= 1
        if char.isspace() and depth == 0:
            if buf:
                bits.append(''.join(buf))
                buf = []
            continue
        buf.append(char)
    if buf:
        bits.append(''.join(buf))
    return bits


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in '"\'':
        return token[1:-1]
    return token


def _render(
    nodes: list[Node],
    *,
    scopes: list[Any],
    blocks: list[dict[str, Any]],
    frames: list[dict[str, Any]],
    helpers: dict[str, HelperFn],
    partials: dict[str, Any],
    escape_html: bool,
    strict: bool,
    reserved_data_keys: set[str] | None = None,
    raw_data: dict[str, Any] | None = None,
    depth: int = 0,
    max_depth: int = _MAX_DEPTH,
) -> str:
    if depth > max_depth:
        raise TemplateRecursionError(f'maximum template depth exceeded ({max_depth})')
    out: list[str] = []
    for node in nodes:
        if isinstance(node, InlinePartial):
            partials = dict(partials)
            partials[node.name] = node.body
            continue
        out.append(
            _render_one(
                node,
                scopes=scopes,
                blocks=blocks,
                frames=frames,
                helpers=helpers,
                partials=partials,
                escape_html=escape_html,
                strict=strict,
                reserved_data_keys=reserved_data_keys,
                raw_data=raw_data,
                depth=depth + 1,
                max_depth=max_depth,
            )
        )
    return ''.join(out)


_BUILTINS = ('if', 'unless', 'each', 'with')

_ESCAPE = str.maketrans({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '`': '&#x60;',
    '=': '&#x3D;',
})


def _render_one(node: Node, **env: Any) -> str:
    if isinstance(node, Text):
        return node.value
    if isinstance(node, Mustache):
        value = _eval_call(node.call, block=None, **env)
        return _show(value, raw=node.raw, escape_html=env['escape_html'])
    if isinstance(node, Block):
        value = _eval_block(node, **env)
        if isinstance(value, Rendered):
            return str(value)
        return _show(value, raw=False, escape_html=env['escape_html'])
    if isinstance(node, Partial):
        return _render_partial(node.name, node.context_path, None, node.hash, node.indent, **env)
    if isinstance(node, PartialBlock):
        return _render_partial(node.name, node.context_path, node.body, node.hash, '', **env)
    return ''


def _eval_block(node: Block, **env: Any) -> Rendered | Any:
    name: str = node.call['name']
    if name == 'if':
        show, _ = _if_condition(node, **env)
        return Rendered(_choose(show, node, **env))
    if name == 'unless':
        show, _ = _if_condition(node, label='unless', **env)
        return Rendered(_choose(not show, node, **env))
    if name == 'with':
        return Rendered(_with_block(node, **env))
    if name == 'each':
        return Rendered(_each(node, **env))
    called = node.call.get('literal') or name in env['helpers'] or node.call['args'] or node.call['hash']
    if called:
        return _eval_call(node.call, block=node, **env)
    return Rendered(_section(node, **env))


def _if_condition(node: Block, *, label: str = 'if', **env: Any) -> tuple[bool, Any]:
    args: list[str] = node.call['args']
    if len(args) != 1:
        raise ValueError(f'#{label} requires exactly one argument')
    value = _value(args[0], **_loose(env))
    include_zero = False
    token = node.call['hash'].get('includeZero')
    if token is not None:
        include_zero = _value(token, **_loose(env)) is True
    return _if_shows(value, include_zero=include_zero), value


def _choose(show: bool, node: Block, **env: Any) -> str:
    return _render(node.body if show else node.inverse, **env)


def _with_block(node: Block, **env: Any) -> str:
    args: list[str] = node.call['args']
    if len(args) != 1:
        raise ValueError('#with requires exactly one argument')
    ctx = _reject_function(_value(args[0], **_loose(env)))
    if _is_empty(ctx):
        return _render(node.inverse, **env)
    return _render(node.body, **_pushed(env, ctx, _param_scope(node.call['params'], ctx, None)))


def _each(node: Block, **env: Any) -> str:
    if len(node.call['args']) != 1:
        raise ValueError('Must pass iterator to #each')
    items = _reject_function(_value(node.call['args'][0], **_loose(env)))
    return _iterate(items, node.body, node.inverse, node.call['params'], env)


def _iterate(items: Any, body: list[Node], inverse: list[Node], params: list[str], env: dict[str, Any]) -> str:
    if isinstance(items, Mapping):
        pairs: list[tuple[Any, Any]] = list(items.items())
    elif isinstance(items, Sequence) and not isinstance(items, (str, bytes)):
        pairs = list(enumerate(items))
    else:
        return _render(inverse, **env)
    if not pairs:
        return _render(inverse, **env)
    parts: list[str] = []
    for index, (key, item) in enumerate(pairs):
        parent: dict[str, Any] = env['frames'][-1]
        frame = {**parent, 'key': key, 'index': index, 'first': index == 0, 'last': index == len(pairs) - 1}
        parts.append(_render(body, **_pushed(env, item, _param_scope(params, item, key), frame)))
    return ''.join(parts)


def _section(node: Block, **env: Any) -> str:
    """{{#name}} when name is not a helper. A list repeats. Anything else enters once."""
    value = _reject_function(_value(node.call['name'], **env))
    if value is True:
        # This branch keeps the current value. as |name| is not filled in,
        # and reading that name raises.
        params: list[str] = node.call['params']
        if params:
            env = {**env, 'blocks': [*env['blocks'], {name: _Unbound() for name in params}]}
        return _render(node.body, **env)
    if value is False or value is None:
        return _render(node.inverse, **env)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return _iterate(value, node.body, node.inverse, node.call['params'], env)
    # A single value steps in. as |name| does not bind it; {{name}} still reads the value.
    return _render(node.body, **_pushed(env, value, {}))


def _param_scope(params: list[str], value: Any, key: Any) -> dict[str, Any]:
    scope: dict[str, Any] = {}
    if not params:
        return scope
    scope[params[0]] = value
    if len(params) > 1:
        scope[params[1]] = key
    return scope


def _pushed(
    env: dict[str, Any],
    ctx: Any,
    param_scope: dict[str, Any],
    frame: dict[str, Any] | None = None,
) -> dict[str, Any]:
    frames = env['frames'] if frame is None else [*env['frames'], frame]
    return {
        **env,
        'scopes': [*env['scopes'], ctx],
        'blocks': [*env['blocks'], param_scope],
        'frames': frames,
    }


def _eval_call(call: dict[str, Any], *, block: Block | None, as_call: bool = False, **env: Any) -> Any:
    name: str = call['name']
    if name in _BUILTINS and block is not None:
        return _eval_block(Block(call, block.body, block.inverse), **env)
    helper = env['helpers'].get(name)
    args = [_value(bit, **_loose(env)) for bit in call['args']]
    hashed = {key: _value(bit, **_loose(env)) for key, bit in call['hash'].items()}

    def fn(context: Any | None = None) -> SafeString:
        if block is None:
            return SafeString('')
        pushed = env if context is None else _pushed(env, context, {})
        # The block body is already rendered. Returning it plain would escape it again.
        return SafeString(_render(block.body, **pushed))

    def inverse(context: Any | None = None) -> SafeString:
        if block is None:
            return SafeString('')
        pushed = env if context is None else _pushed(env, context, {})
        return SafeString(_render(block.inverse, **pushed))

    if helper is None and not as_call and block is None and not call['args'] and not call['hash']:
        # {{"name"}} calls a helper. It is not text, and it is not a field.
        if call.get('literal'):
            return None
        return _value(name, **env)
    if helper is None:
        raise ValueError(f'Missing helper: "{name}"')
    return helper(
        args,
        Options(
            hash=hashed,
            fn=fn,
            inverse=inverse,
            data=env['frames'][-1],
            context=env['scopes'][-1],
            is_block=block is not None,
        ),
    )


def _loose(env: dict[str, Any]) -> dict[str, Any]:
    return {**env, 'strict': False}


def _value(token: str, **env: Any) -> Any:
    if token.startswith('(') and token.endswith(')'):
        return _eval_call(_call(token[1:-1].strip()), block=None, as_call=True, **env)
    if len(token) >= 2 and token[0] == token[-1] and token[0] in '"\'':
        return _unescape(token)
    if token == 'true':
        return True
    if token == 'false':
        return False
    number = _number(token)
    if number is not None:
        return number
    if token.startswith('.') and token[1:].isdigit():
        raise ValueError(f'{token} is not a valid number')
    return _path(token, **env)


def _unescape(token: str) -> str:
    # Only an escaped quote is special. \n stays a backslash and an n.
    body = token[1:-1]
    if token[0] == '"':
        return body.replace('\\"', '"')
    return body.replace("\\'", "'")


def _number(token: str) -> int | float | None:
    body = token[1:] if token.startswith('-') else token
    if not body or body.count('.') > 1:
        return None
    head, dot, tail = body.partition('.')
    if dot:
        # .5 and 1. are not numbers. .5 is rejected by the caller.
        if not head.isdigit() or not tail.isdigit():
            return None
        return float(token)
    if head.isdigit():
        return int(token)
    return None


def _path(path: str, **env: Any) -> Any:
    if path.startswith('@'):
        return _data_path(path[1:], original=path, **env)
    return _context_path(path, original=path, **env)


def _context_path(path: str, *, original: str, **env: Any) -> Any:
    strict: bool = env['strict']
    parts = _parts(path)
    scopes: list[Any] = env['scopes']
    blocks: list[dict[str, Any]] = env['blocks']
    index = 0
    climbed = 0
    while index < len(parts) and parts[index] == '..':
        scopes = scopes[:-1]
        climbed += 1
        index += 1
        if not scopes:
            if strict:
                raise StrictModeError(original)
            return None
    if index >= len(parts):
        return _reject_function(scopes[-1])
    first = parts[index]
    current = _MISSING
    # An outer {{#each as |name|}} stays visible inside the inner one.
    # ../name reads the parent value, not that name.
    if climbed == 0 and first not in ('.', 'this'):
        for frame in reversed(blocks):
            if first in frame:
                current = frame[first]
                break
    if isinstance(current, _Unbound):
        raise ValueError(f'{first} is not defined')
    if current is _MISSING:
        if first in ('.', 'this'):
            current = scopes[-1]
        else:
            current = _step(scopes[-1], first, strict=strict, original=original)
    index += 1
    for part in parts[index:]:
        if part in ('.', 'this'):
            continue
        current = _step(current, part, strict=strict, original=original)
    return _reject_function(current)


def _data_path(path: str, *, original: str, **env: Any) -> Any:
    strict: bool = env['strict']
    reserved_keys: set[str] | None = env.get('reserved_data_keys')
    raw_data: dict[str, Any] = env.get('raw_data', {})
    parts = _parts(path)
    frames: list[dict[str, Any]] = env['frames']
    current: Any = frames[-1]
    for part in parts:
        if part == '..':
            frames = frames[:-1]
            current = frames[-1] if frames else None
            if current is None:
                if strict:
                    raise StrictModeError(original)
                return None
            continue
        if reserved_keys and part in reserved_keys and part in raw_data:
            raise ValueError(f'runtime data key {part!r} is reserved')
        current = _step(current, part, strict=strict, original=original)
    return current


def _step(current: Any, part: str, *, strict: bool, original: str) -> Any:
    if isinstance(current, Mapping) and part in current:
        return current[part]
    if isinstance(current, Sequence) and not isinstance(current, (str, bytes)) and str(part).isdigit():
        index = int(part)
        if 0 <= index < len(current):
            return current[index]
    if strict:
        raise StrictModeError(original)
    return None


def _is_quoted(token: str) -> bool:
    return len(token) >= 2 and token[0] == token[-1] and token[0] in '"\''


def _check_token(token: str) -> None:
    if _is_quoted(token) or (token.startswith('(') and token.endswith(')')):
        return
    if _number(token) is not None:
        return
    if token.startswith('.') and token[1:].isdigit():
        raise ValueError(f'{token} is not a valid number')
    if token.startswith('@'):
        if len(token) == 1:
            raise ValueError(f'{token} is not valid')
        _parts(token[1:])
        return
    _parts(token)


def _id_char(char: str) -> bool:
    """A character that can appear in a name. List indexes use brackets instead."""
    if char.isspace() or char in '!"#./@`':
        return False
    code = ord(char)
    if 0x25 <= code <= 0x2C or 0x3B <= code <= 0x3E:
        return False
    if 0x5B <= code <= 0x5E or 0x7B <= code <= 0x7E:
        return False
    return True


def _push_segment(parts: list[str], buf: list[str], path: str) -> None:
    if not buf:
        return
    segment = ''.join(buf)
    # items.0 is not a path. The index form is items.[0].
    if _number(segment) is not None or not all(_id_char(char) for char in segment):
        raise ValueError(f'{path} is not valid')
    parts.append(segment)


def _parts(path: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(path):
        char = path[i]
        if char == '[':
            _push_segment(parts, buf, path)
            buf = []
            end = path.find(']', i + 1)
            if end < 0:
                raise ValueError('unclosed path')
            parts.append(path[i + 1 : end])
            i = end + 1
            if i < len(path) and path[i] in './':
                i += 1
            continue
        if char in './':
            if path.startswith('..', i):
                _push_segment(parts, buf, path)
                buf = []
                parts.append('..')
                i += 2
                if i < len(path) and path[i] in './':
                    i += 1
                continue
            had_segment = bool(buf)
            _push_segment(parts, buf, path)
            buf = []
            # A dot after a name is only the separator. A leading dot is "this".
            if char == '.' and not had_segment:
                parts.append('.')
            i += 1
            continue
        buf.append(char)
        i += 1
    _push_segment(parts, buf, path)
    return parts


def _is_empty(value: Any) -> bool:
    """What {{#with}} treats as nothing to step into.

    An empty object was still passed. A list with no items was not.
    """
    if value is None or value is False or value == '':
        return True
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 0


def _if_shows(value: Any, *, include_zero: bool) -> bool:
    """What {{#if}} treats as yes. 0 is no, unless includeZero=true."""
    if isinstance(value, bool):
        return value
    if value == 0 and not include_zero:
        return False
    return not _is_empty(value)


def _reject_function(value: Any) -> Any:
    # A template renders data. A function in the input is not called.
    if callable(value):
        raise ValueError('the input contains a function; register it as a helper')
    return value


def _show(value: Any, *, raw: bool, escape_html: bool) -> str:
    value = _reject_function(value)
    text = _js_text(value)
    if isinstance(value, SafeString) or raw or not escape_html:
        return text
    return text.translate(_ESCAPE)


def _js_text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return ','.join(_js_text(item) for item in value)
    if isinstance(value, Mapping):
        return '[object Object]'
    return str(value)


def _render_partial(
    name: str,
    context_path: str | None,
    fallback: list[Node] | None,
    hashed_tokens: dict[str, str],
    indent: str,
    **env: Any,
) -> str:
    if name.startswith('('):
        evaluated_name = _value(name, **_loose(env))
        if not isinstance(evaluated_name, str):
            raise ValueError('a partial name must be a string')
        name = evaluated_name
    if name == '@partial-block':
        body = env['frames'][-1].get('partial-block')
        if not body:
            raise ValueError('The partial @partial-block could not be found')
        return _render(body, **env)
    program = env['partials'].get(name)
    if program is None:
        if fallback is not None:
            return _render(fallback, **env)
        raise ValueError(f'The partial {name} could not be found')
    if isinstance(program, str):
        program = compile_template(program, max_depth=env.get('max_depth', _MAX_DEPTH))
        env['partials'][name] = program
    hashed = {key: _value(token, **_loose(env)) for key, token in hashed_tokens.items()}
    context = env['scopes'][-1]
    if context_path:
        context = _value(context_path, **_loose(env))
    if hashed:
        context = _overlay(context, hashed)
    context = _reject_function(context)
    frames = env['frames']
    if fallback is not None:
        frames = [*frames[:-1], {**frames[-1], 'partial-block': fallback}]
    # A partial starts over. {{../name}} does not see the caller. {{@index}} and {{@root}} do.
    text = _render(
        program,
        scopes=[context],
        blocks=[{}],
        frames=frames,
        helpers=env['helpers'],
        partials=env['partials'],
        escape_html=env['escape_html'],
        strict=env['strict'],
        reserved_data_keys=env.get('reserved_data_keys'),
        raw_data=env.get('raw_data'),
        depth=env.get('depth', 0),
        max_depth=env.get('max_depth', _MAX_DEPTH),
    )
    return _apply_indent(text, indent)


def _apply_indent(text: str, indent: str) -> str:
    if not indent or text == '':
        return text
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if line == '' and index == len(lines) - 1:
            break
        lines[index] = indent + line
    return '\n'.join(lines)


def _overlay(base: Any, hashed: dict[str, Any]) -> Any:
    if not hashed:
        return base
    if isinstance(base, Mapping):
        return {**base, **hashed}
    return dict(hashed)
