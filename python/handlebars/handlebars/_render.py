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


class _Unbound:
    """A block param named on {{#yes as |name|}}. That branch never assigns it."""


_MISSING = object()


class StrictModeError(Exception):
    """Raised when a path is missing and strict mode is on."""

    def __init__(self, path):
        self.path = path
        super().__init__(f'{path} is not defined')


class Text:
    """Characters copied into the output unchanged."""

    def __init__(self, value):
        self.value = value


class Mustache:
    """A {{name}} or {{{name}}} tag."""

    def __init__(self, call, raw):
        self.call = call
        self.raw = raw


class Block:
    """A {{#name}} body and its else body."""

    def __init__(self, call, body, inverse):
        self.call = call
        self.body = body
        self.inverse = inverse


class Partial:
    """A {{> name}} inclusion."""

    def __init__(self, name, context_path, hash=None, indent=''):
        self.name = name
        self.context_path = context_path
        self.hash = hash or {}
        self.indent = indent


class PartialBlock:
    """A {{#> name}} block. The body renders when the partial is missing."""

    def __init__(self, name, body, context_path=None, hash=None):
        self.name = name
        self.body = body
        self.context_path = context_path
        self.hash = hash or {}


class Rendered(str):
    """Text that already went through the template, so it is not escaped again."""


class InlinePartial:
    """A partial defined inside the template with {{#*inline}}."""

    def __init__(self, name, body):
        self.name = name
        self.body = body


def compile_template(source):
    """Parses a template into nodes. Raises ValueError when a tag is unclosed."""
    return _parse(_tokens(source))


def render_program(program, context, *, data, helpers, partials, escape_html, strict):
    """Renders parsed nodes. data is the dict {{@name}} reads.

    @root is the input. A data dict that already contains root replaces it.
    """
    frame = {'root': context, **(data or {})}
    return _render(
        program,
        scopes=[context],
        blocks=[{}],
        frames=[frame],
        helpers=helpers,
        partials=dict(partials),
        escape_html=escape_html,
        strict=strict,
    )


def _tokens(source):
    parts = []
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
            raise ValueError('raw blocks are not supported')
        # {{!-- comments end at --}}, so a }} inside one is still comment text.
        long_end = _long_comment_end(source, start)
        if long_end is not None:
            end, closer = long_end
            triple = False
        else:
            triple = source.startswith('{{{', start)
            if triple:
                end = source.find('}}}', start + 3)
                closer = 3
            else:
                end = source.find('}}', start + 2)
                closer = 2
            if end < 0:
                raise ValueError('unclosed tag')
        body = source[start + closer : end]
        strip_before = body.startswith('~')
        strip_after = body.endswith('~')
        body = body[1:] if strip_before else body
        body = body[:-1] if strip_after else body
        parts.append(('tag', body.strip(), triple, strip_before, strip_after, False, ''))
        i = end + closer
    return _drop_standalone_lines(_strip_neighbors(parts))


def _long_comment_end(source, start):
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


def _strip_neighbors(parts):
    for index, part in enumerate(parts):
        if not isinstance(part, tuple):
            continue
        _, _, _, strip_before, strip_after, _, _ = part
        if strip_before and index and isinstance(parts[index - 1], str):
            parts[index - 1] = parts[index - 1].rstrip()
        if strip_after and index + 1 < len(parts) and isinstance(parts[index + 1], str):
            parts[index + 1] = parts[index + 1].lstrip()
    return parts


def _drop_standalone_lines(parts):
    """A block, partial, or comment alone on a line does not leave that blank line.

    Which tags qualify is decided from the original line breaks. Dropping one
    tag's newline must not hide that the next tag is also alone on its line.
    """
    planned = []
    for index, part in enumerate(parts):
        if not isinstance(part, tuple) or not _standalone_tag(part[1]):
            continue
        if not _starts_line(parts, index):
            continue
        line_end = _line_ending_after(parts, index)
        if line_end is None:
            continue
        indent = _indent_before(parts, index) if part[1].startswith('>') else ''
        planned.append((index, line_end, indent))
    for index, line_end, indent in planned:
        _trim_indent_before(parts, index)
        part = parts[index]
        parts[index] = (*part[:6], indent)
        if line_end:
            nxt = parts[index + 1]
            parts[index + 1] = nxt[line_end:]
    return parts


def _starts_line(parts, index):
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


def _line_ending_after(parts, index):
    """How many characters of the following line ending to drop, or None."""
    if index + 1 >= len(parts):
        return 0
    nxt = parts[index + 1]
    if not isinstance(nxt, str):
        return None
    line_end = _standalone_line_end(nxt)
    if nxt and line_end is None:
        return None
    return len(line_end)


def _trim_indent_before(parts, index):
    for cursor in range(index - 1, -1, -1):
        part = parts[cursor]
        if not isinstance(part, str):
            return
        newline = part.rfind('\n')
        if newline >= 0:
            parts[cursor] = part[: newline + 1]
            return
        parts[cursor] = ''


def _standalone_line_end(text):
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


def _indent_before(parts, index):
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


def _standalone_tag(body):
    if body.startswith(('!', '#', '/', '>', '^')):
        return True
    return body == 'else' or body.startswith('else ')


def _parse(parts):
    nodes, index = _until(parts, 0, None)
    if index != len(parts):
        raise ValueError('unexpected closing tag')
    return nodes


def _until(parts, index, stop):
    nodes = []
    while index < len(parts):
        part = parts[index]
        index += 1
        if isinstance(part, str):
            if part:
                nodes.append(Text(part))
            continue
        _, body, triple, _, _, _, indent = part
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
            inverse, index = _until(parts, index, stop)
            if body.startswith('else if ') or body.startswith('else unless '):
                cond = body[len('else ') :]
                nested_body, nested_else = _pop_trailing_else(inverse)
                inverse = [Block(_call(cond), nested_body, nested_else)]
            nodes.append(('else', inverse))
            return nodes, index
        if body.startswith('#*inline'):
            name = _unquote(body.split(None, 2)[1])
            inner, index = _until(parts, index, 'inline')
            nodes.append(InlinePartial(name, _without_else(inner)))
            continue
        if body.startswith('#>'):
            call = _call(body[2:].strip())
            inner, index = _until(parts, index, call['name'])
            context_path = call['args'][0] if call['args'] else None
            nodes.append(PartialBlock(call['name'], _without_else(inner), context_path, call['hash']))
            continue
        if body.startswith('#') or body.startswith('^'):
            inverse_section = body.startswith('^')
            call = _call(body[1:])
            inner, index = _until(parts, index, call['name'])
            body_nodes, inverse = _split_else(inner)
            if inverse_section:
                body_nodes, inverse = inverse, body_nodes
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


def _split_else(nodes):
    if nodes and isinstance(nodes[-1], tuple) and nodes[-1][0] == 'else':
        return nodes[:-1], nodes[-1][1]
    return nodes, []


def _without_else(nodes):
    body, _ = _split_else(nodes)
    return body


def _pop_trailing_else(nodes):
    return _split_else(nodes)


def _call(header):
    params = []
    if ' as |' in header:
        header, rest = header.split(' as |', 1)
        params = rest.rstrip('|').split()
    bits = _args(header.strip())
    hashed = {}
    positional = []
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


def _args(text):
    bits = []
    buf = []
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


def _unquote(token):
    if len(token) >= 2 and token[0] == token[-1] and token[0] in '"\'':
        return token[1:-1]
    return token


def _render(nodes, *, scopes, blocks, frames, helpers, partials, escape_html, strict):
    out = []
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


def _render_one(node, **env):
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


def _eval_block(node, **env):
    name = node.call['name']
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


def _if_condition(node, *, label='if', **env):
    args = node.call['args']
    if len(args) != 1:
        raise ValueError(f'#{label} requires exactly one argument')
    value = _value(args[0], **_loose(env))
    include_zero = False
    token = node.call['hash'].get('includeZero')
    if token is not None:
        include_zero = _value(token, **_loose(env)) is True
    return _if_shows(value, include_zero=include_zero), value


def _choose(show, node, **env):
    return _render(node.body if show else node.inverse, **env)


def _with_block(node, **env):
    args = node.call['args']
    if len(args) != 1:
        raise ValueError('#with requires exactly one argument')
    ctx = _reject_function(_value(args[0], **_loose(env)))
    if _is_empty(ctx):
        return _render(node.inverse, **env)
    return _render(node.body, **_pushed(env, ctx, _param_scope(node.call['params'], ctx, None)))


def _each(node, **env):
    if len(node.call['args']) != 1:
        raise ValueError('Must pass iterator to #each')
    items = _reject_function(_value(node.call['args'][0], **_loose(env)))
    return _iterate(items, node.body, node.inverse, node.call['params'], env)


def _iterate(items, body, inverse, params, env):
    if isinstance(items, dict):
        pairs = list(items.items())
    elif isinstance(items, list):
        pairs = list(enumerate(items))
    else:
        return _render(inverse, **env)
    if not pairs:
        return _render(inverse, **env)
    parts = []
    for index, (key, item) in enumerate(pairs):
        parent = env['frames'][-1]
        frame = {**parent, 'key': key, 'index': index, 'first': index == 0, 'last': index == len(pairs) - 1}
        parts.append(_render(body, **_pushed(env, item, _param_scope(params, item, key), frame)))
    return ''.join(parts)


def _section(node, **env):
    """{{#name}} when name is not a helper. A list repeats. Anything else enters once."""
    value = _reject_function(_value(node.call['name'], **env))
    if value is True:
        # This branch keeps the current value. as |name| is not filled in,
        # and reading that name raises.
        params = node.call['params']
        if params:
            env = {**env, 'blocks': [*env['blocks'], {name: _Unbound() for name in params}]}
        return _render(node.body, **env)
    if value is False or value is None:
        return _render(node.inverse, **env)
    if isinstance(value, list):
        return _iterate(value, node.body, node.inverse, node.call['params'], env)
    # A single value steps in. as |name| does not bind it; {{name}} still reads the value.
    return _render(node.body, **_pushed(env, value, {}))


def _param_scope(params, value, key):
    scope = {}
    if not params:
        return scope
    scope[params[0]] = value
    if len(params) > 1:
        scope[params[1]] = key
    return scope


def _pushed(env, ctx, param_scope, frame=None):
    frames = env['frames'] if frame is None else [*env['frames'], frame]
    return {
        **env,
        'scopes': [*env['scopes'], ctx],
        'blocks': [*env['blocks'], param_scope],
        'frames': frames,
    }


def _eval_call(call, *, block, as_call=False, **env):
    from handlebars.compiler import Options

    name = call['name']
    if name in _BUILTINS and block is not None:
        return _eval_block(Block(call, block.body, block.inverse), **env)
    helper = env['helpers'].get(name)
    args = [_value(bit, **_loose(env)) for bit in call['args']]
    hashed = {key: _value(bit, **_loose(env)) for key, bit in call['hash'].items()}

    def fn(context=None):
        from handlebars.compiler import SafeString

        if block is None:
            return ''
        pushed = env if context is None else _pushed(env, context, {})
        # The block body is already rendered. Returning it plain would escape it again.
        return SafeString(_render(block.body, **pushed))

    def inverse(context=None):
        from handlebars.compiler import SafeString

        if block is None:
            return ''
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


def _loose(env):
    return {**env, 'strict': False}


def _value(token, **env):
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


def _unescape(token):
    # Only an escaped quote is special. \n stays a backslash and an n.
    body = token[1:-1]
    if token[0] == '"':
        return body.replace('\\"', '"')
    return body.replace("\\'", "'")


def _number(token):
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


def _path(path, **env):
    if path.startswith('@'):
        return _data_path(path[1:], original=path, **env)
    return _context_path(path, original=path, **env)


def _context_path(path, *, original, **env):
    strict = env['strict']
    parts = _parts(path)
    scopes = env['scopes']
    blocks = env['blocks']
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


def _data_path(path, *, original, **env):
    strict = env['strict']
    parts = _parts(path)
    frames = env['frames']
    current = frames[-1]
    for part in parts:
        if part == '..':
            frames = frames[:-1]
            current = frames[-1] if frames else None
            if current is None:
                if strict:
                    raise StrictModeError(original)
                return None
            continue
        current = _step(current, part, strict=strict, original=original)
    return current


def _step(current, part, *, strict, original):
    if isinstance(current, dict) and part in current:
        return current[part]
    if isinstance(current, list) and str(part).isdigit():
        index = int(part)
        if 0 <= index < len(current):
            return current[index]
    if strict:
        raise StrictModeError(original)
    return None


def _is_quoted(token):
    return len(token) >= 2 and token[0] == token[-1] and token[0] in '"\''


def _check_token(token):
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


def _id_char(char):
    """A character that can appear in a name. List indexes use brackets instead."""
    if char.isspace() or char in '!"#./@`':
        return False
    code = ord(char)
    if 0x25 <= code <= 0x2C or 0x3B <= code <= 0x3E:
        return False
    if 0x5B <= code <= 0x5E or 0x7B <= code <= 0x7E:
        return False
    return True


def _push_segment(parts, buf, path):
    if not buf:
        return
    segment = ''.join(buf)
    # items.0 is not a path. The index form is items.[0].
    if _number(segment) is not None or not all(_id_char(char) for char in segment):
        raise ValueError(f'{path} is not valid')
    parts.append(segment)


def _parts(path):
    parts = []
    buf = []
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


def _is_empty(value):
    """What {{#with}} treats as "nothing to enter"."""
    if value is None or value is False or value == '':
        return True
    return isinstance(value, list) and len(value) == 0


def _if_shows(value, *, include_zero):
    """What {{#if}} treats as yes. 0 is no, unless includeZero=true."""
    if isinstance(value, bool):
        return value
    if value == 0 and not include_zero:
        return False
    return not _is_empty(value)


def _reject_function(value):
    # A template renders data. A function in the input is not called.
    if callable(value):
        raise ValueError('the input contains a function; register it as a helper')
    return value


def _show(value, *, raw, escape_html):
    from handlebars.compiler import SafeString

    value = _reject_function(value)
    text = _js_text(value)
    if isinstance(value, SafeString) or raw or not escape_html:
        return text
    return text.translate(_ESCAPE)


def _js_text(value):
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
    if isinstance(value, list):
        return ','.join(_js_text(item) for item in value)
    if isinstance(value, dict):
        return '[object Object]'
    return str(value)


def _render_partial(name, context_path, fallback, hashed_tokens, indent, **env):
    if name.startswith('('):
        name = _value(name, **_loose(env))
        if not isinstance(name, str):
            raise ValueError('a partial name must be a string')
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
        program = compile_template(program)
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
    )
    return _apply_indent(text, indent)


def _apply_indent(text, indent):
    if not indent or text == '':
        return text
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if line == '' and index == len(lines) - 1:
            break
        lines[index] = indent + line
    return '\n'.join(lines)


def _overlay(base, hashed):
    if not hashed:
        return base
    if isinstance(base, dict):
        return {**base, **hashed}
    return dict(hashed)
