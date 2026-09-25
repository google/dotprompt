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

import html


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

    def __init__(self, name, context_path, hash=None):
        self.name = name
        self.context_path = context_path
        self.hash = hash or {}


class PartialBlock:
    """A {{#> name}} block. The body renders when the partial is missing."""

    def __init__(self, name, body):
        self.name = name
        self.body = body


class InlinePartial:
    """A partial defined inside the template with {{#*inline}}."""

    def __init__(self, name, body):
        self.name = name
        self.body = body


def compile_template(source):
    """Parses a template into nodes. Raises ValueError when a tag is unclosed."""
    return _parse(_tokens(source))


def render_program(program, context, *, data, helpers, partials, escape_html, strict):
    """Renders parsed nodes. data is the dict {{@name}} reads."""
    data_dict = data or {}
    partials_dict = dict(partials)
    if 'root' in data_dict and _reads_at_root(program, partials_dict):
        raise ValueError("runtime data key 'root' is reserved")
    clean_data = {k: v for k, v in data_dict.items() if k != 'root'}
    return _render(
        program,
        scopes=[context],
        frame={'root': context, **clean_data},
        helpers=helpers,
        partials=partials_dict,
        escape_html=escape_html,
        strict=strict,
    )


def _reads_at_root(nodes, partials, seen_partials=None):
    if seen_partials is None:
        seen_partials = set()
    for node in nodes:
        if isinstance(node, Mustache):
            if _call_reads_at_root(node.call):
                return True
        elif isinstance(node, Block):
            if _call_reads_at_root(node.call):
                return True
            if _reads_at_root(node.body, partials, seen_partials):
                return True
            if _reads_at_root(node.inverse, partials, seen_partials):
                return True
        elif isinstance(node, Partial):
            if _call_reads_at_root({
                'name': node.name,
                'args': [node.context_path] if node.context_path else [],
                'hash': node.hash,
                'params': [],
            }):
                return True
            if node.name not in seen_partials:
                seen_partials.add(node.name)
                part = partials.get(node.name)
                if isinstance(part, str):
                    part = compile_template(part)
                    partials[node.name] = part
                if isinstance(part, list) and _reads_at_root(part, partials, seen_partials):
                    return True
        elif isinstance(node, PartialBlock):
            if _reads_at_root(node.body, partials, seen_partials):
                return True
            if node.name not in seen_partials:
                seen_partials.add(node.name)
                part = partials.get(node.name)
                if isinstance(part, str):
                    part = compile_template(part)
                    partials[node.name] = part
                if isinstance(part, list) and _reads_at_root(part, partials, seen_partials):
                    return True
    return False


def _call_reads_at_root(call):
    if _token_reads_at_root(call.get('name', '')):
        return True
    for arg in call.get('args', []):
        if _token_reads_at_root(arg):
            return True
    for val in call.get('hash', {}).values():
        if _token_reads_at_root(val):
            return True
    return False


def _token_reads_at_root(token):
    if not isinstance(token, str):
        return False
    if token.startswith('(') and token.endswith(')'):
        return any(_token_reads_at_root(b) for b in _args(token[1:-1].strip()))
    if len(token) >= 2 and token[0] == token[-1] and token[0] in '"\'':
        return False
    return token == '@root' or token.startswith('@root.') or token.startswith('@root/')


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
        if slashes % 2 == 1:
            parts.append(source[i : start - 1] + '{{')
            i = start + 2
            continue
        if start > i:
            parts.append(source[i:start])
        if source.startswith('{{{{raw}}}}', start):
            end = source.find('{{{{/raw}}}}', start)
            if end < 0:
                raise ValueError('unclosed block')
            parts.append(source[start + len('{{{{raw}}}}') : end])
            i = end + len('{{{{/raw}}}}')
            continue
        raw_block = source.startswith('{{{{', start)
        triple = source.startswith('{{{', start) and not raw_block
        if raw_block:
            end = source.find('}}}}', start + 4)
            closer = 4
        elif triple:
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
        parts.append(('tag', body.strip(), triple or raw_block, strip_before, strip_after, raw_block))
        i = end + closer
    return _drop_standalone_lines(_strip_neighbors(parts))


def _strip_neighbors(parts):
    for index, part in enumerate(parts):
        if not isinstance(part, tuple):
            continue
        _, _, _, strip_before, strip_after, _ = part
        if strip_before and index and isinstance(parts[index - 1], str):
            parts[index - 1] = parts[index - 1].rstrip()
        if strip_after and index + 1 < len(parts) and isinstance(parts[index + 1], str):
            parts[index + 1] = parts[index + 1].lstrip()
    return parts


def _drop_standalone_lines(parts):
    """A block, partial, or comment alone on a line does not leave that blank line."""
    for index, part in enumerate(parts):
        if not isinstance(part, tuple) or not _standalone_tag(part[1]):
            continue
        if not _starts_line(parts, index):
            continue
        line_end = _line_ending_after(parts, index)
        if line_end is None:
            continue
        _trim_indent_before(parts, index)
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


def _standalone_tag(body):
    if body.startswith(('!', '#', '/', '>')):
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
        _, body, triple, _, _, raw_block = part
        if body.startswith('!'):
            continue
        if body.startswith('/'):
            name = body[1:].split()[0]
            if stop != name:
                raise ValueError(f'unexpected closing tag {name}')
            return nodes, index
        if body == 'else' or body.startswith('else '):
            if stop is None:
                raise ValueError('{{else}} outside a block')
            inverse, index = _until(parts, index, stop)
            if body.startswith('else if '):
                cond = body[len('else if ') :]
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
            name = body[2:].strip().split()[0]
            inner, index = _until(parts, index, name)
            nodes.append(PartialBlock(name, _without_else(inner)))
            continue
        if body.startswith('#'):
            call = _call(body[1:])
            inner, index = _until(parts, index, call['name'])
            body_nodes, inverse = _split_else(inner)
            nodes.append(Block(call, body_nodes, inverse))
            continue
        if body.startswith('>'):
            call = _call(body[1:].strip())
            context_path = call['args'][0] if call['args'] else None
            nodes.append(Partial(call['name'], context_path, call['hash']))
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
            hashed[key] = value
        else:
            positional.append(bit)
    return {'name': positional[0], 'args': positional[1:], 'hash': hashed, 'params': params}


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
        if char == '(':
            depth += 1
        elif char == ')':
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


def _render(nodes, *, scopes, frame, helpers, partials, escape_html, strict):
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
                frame=frame,
                helpers=helpers,
                partials=partials,
                escape_html=escape_html,
                strict=strict,
            )
        )
    return ''.join(out)


def _render_one(node, **env):
    if isinstance(node, Text):
        return node.value
    if isinstance(node, Mustache):
        value = _eval_call(node.call, block=None, **env)
        return _show(value, raw=node.raw, escape_html=env['escape_html'])
    if isinstance(node, Block):
        value = _eval_block(node, **env)
        return '' if value is None else str(value)
    if isinstance(node, Partial):
        return _render_partial(node.name, node.context_path, None, **{**env, 'partial_hash': node.hash})
    if isinstance(node, PartialBlock):
        return _render_partial(node.name, None, node.body, **env)
    return ''


def _eval_block(node, **env):
    name = node.call['name']
    if name == 'if':
        value = _value(node.call['args'][0], **env) if node.call['args'] else None
        chosen = node.body if _truthy(value) else node.inverse
        return _render(chosen, **env)
    if name == 'unless':
        value = _value(node.call['args'][0], **env) if node.call['args'] else None
        chosen = node.inverse if _truthy(value) else node.body
        return _render(chosen, **env)
    if name == 'with':
        ctx = _value(node.call['args'][0], **env) if node.call['args'] else None
        if ctx is None or ctx is False:
            return _render(node.inverse, **env)
        scopes = [*env['scopes'], ctx]
        return _render(node.body, **{**env, 'scopes': scopes})
    if name == 'each':
        return _each(node, **env)
    return _eval_call(node.call, block=node, **env)


def _each(node, **env):
    items = _value(node.call['args'][0], **env) if node.call['args'] else None
    if items is None or items == [] or items == {}:
        return _render(node.inverse, **env)
    pairs = list(items.items()) if isinstance(items, dict) else list(enumerate(items))
    object_mode = isinstance(items, dict)
    params = node.call['params']
    parts = []
    for index, (key, item) in enumerate(pairs):
        frame = dict(env['frame'])
        frame.update(index=index, first=index == 0, last=index == len(pairs) - 1)
        if object_mode:
            frame['key'] = key
            frame['index'] = index
        ctx = item
        scopes = [*env['scopes'], ctx]
        if params:
            ctx = dict(ctx) if isinstance(ctx, dict) else {}
            ctx[params[0]] = item
            if len(params) > 1:
                ctx[params[1]] = key if object_mode else index
            scopes = [*env['scopes'], ctx]
        parts.append(_render(node.body, **{**env, 'scopes': scopes, 'frame': frame}))
    return ''.join(parts)


def _eval_call(call, *, block, **env):
    from handlebars.compiler import Options

    helper = env['helpers'].get(call['name'])
    args = [_value(bit, **env) for bit in call['args']]
    hashed = {key: _value(bit, **env) for key, bit in call['hash'].items()}

    def fn(context=None):
        scopes = env['scopes'] if context is None else [*env['scopes'], context]
        if block is None:
            return ''
        return _render(block.body, **{**env, 'scopes': scopes})

    def inverse(context=None):
        scopes = env['scopes'] if context is None else [*env['scopes'], context]
        if block is None:
            return ''
        return _render(block.inverse, **{**env, 'scopes': scopes})

    if helper is None and block is None and not call['args'] and not call['hash']:
        return _value(call['name'], **env)
    if helper is None and block is not None:
        value = _value(call['name'], **env)
        return fn() if _truthy(value) else inverse()
    if helper is None:
        return ''
    return helper(args, Options(hash=hashed, fn=fn, inverse=inverse, data=env['frame'], context=env['scopes'][-1]))


def _value(token, **env):
    if token.startswith('(') and token.endswith(')'):
        return _eval_call(_call(token[1:-1].strip()), block=None, **env)
    if len(token) >= 2 and token[0] == token[-1] and token[0] in '"\'':
        return token[1:-1]
    if token == 'true':
        return True
    if token == 'false':
        return False
    if _number(token) is not None:
        return _number(token)
    return _path(token, **env)


def _number(token):
    try:
        if token.startswith('-') or token.isdigit():
            return int(token)
    except ValueError:
        return None
    return None


def _path(path, **env):
    if path in ('.', 'this'):
        return env['scopes'][-1]
    if path.startswith('../'):
        scopes = env['scopes'][:-1] or [None]
        return _path(path[3:], **{**env, 'scopes': scopes})
    if path.startswith('@'):
        return _dig(env['frame'], path[1:], path, **env)
    return _dig(env['scopes'][-1], path, path, **env)


def _dig(current, path, original, **env):
    for part in path.replace('/', '.').split('.'):
        if part in ('', '.'):
            continue
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
            continue
        if env['strict'] and not (isinstance(current, dict) and part in current):
            raise StrictModeError(original)
        return None
    return current


def _truthy(value):
    return value not in (None, False, '', 0, [])


def _show(value, *, raw, escape_html):
    from handlebars.compiler import SafeString

    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, SafeString) or raw or not escape_html:
        return str(value)
    return html.escape(str(value), quote=True).replace("'", '&#x27;')


def _render_partial(name, context_path, fallback, **env):
    program = env['partials'].get(name)
    if program is None:
        if fallback is not None:
            return _render(fallback, **_render_kwargs(env))
        return ''
    if isinstance(program, str):
        program = compile_template(program)
        env['partials'][name] = program
    scopes = env['scopes']
    hashed = {key: _value(token, **env) for key, token in (env.get('partial_hash') or {}).items()}
    if context_path:
        # {{> card user}} renders the partial against user, not the surrounding input.
        scopes = [*scopes, _overlay(_value(context_path, **env), hashed)]
    elif hashed:
        # {{> greeting name=username}} keeps the current input and adds name.
        scopes = [*scopes[:-1], _overlay(scopes[-1], hashed)]
    return _render(program, **_render_kwargs(env, scopes=scopes))


def _render_kwargs(env, **overrides):
    allowed = ('scopes', 'frame', 'helpers', 'partials', 'escape_html', 'strict')
    kwargs = {key: env[key] for key in allowed}
    kwargs.update(overrides)
    return kwargs


def _overlay(base, hashed):
    if not hashed:
        return base
    if isinstance(base, dict):
        return {**base, **hashed}
    return dict(hashed)
